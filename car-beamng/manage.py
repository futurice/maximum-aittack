#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    manage.py (drive) [--model=<model>] [--js] [--chaos]
    manage.py (train) [--tub=<tub1,tub2,..tubn>]  (--model=<model>) [--base_model=<base_model>] [--no_cache]

Options:
    -h --help        Show this screen.
    --tub TUBPATHS   List of paths to tubs. Comma separated. Use quotes to use wildcards. ie "~/tubs/*"
    --js             Use physical joystick.
    --chaos          Add periodic random steering when manually driving
"""
import os
from docopt import docopt

import donkeycar as dk

# import parts
from donkeycar.parts.camera import PiCamera
from donkeycar.parts.transform import Lambda
from donkeycar.parts.keras import CustomModel
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle
from donkeycar.parts.datastore import TubGroup, TubWriter
from donkeycar.parts.controller import LocalWebController, JoystickController
from donkeycar.parts.clock import Timestamp

import numpy as np
import glob
import json
from PIL import Image

def drive(cfg, model_path=None, use_joystick=False, use_chaos=False):
    """
    Construct a working robotic vehicle from many parts.
    Each part runs as a job in the Vehicle loop, calling either
    it's run or run_threaded method depending on the constructor flag `threaded`.
    All parts are updated one after another at the framerate given in
    cfg.DRIVE_LOOP_HZ assuming each part finishes processing in a timely manner.
    Parts may have named outputs and inputs. The framework handles passing named outputs
    to parts requesting the same named input.
    """

    V = dk.vehicle.Vehicle()

    clock = Timestamp()
    V.add(clock, outputs='timestamp')

    cam = PiCamera(resolution=cfg.CAMERA_RESOLUTION)
    V.add(cam, outputs=['cam/image_array'], threaded=True)

    if use_joystick or cfg.USE_JOYSTICK_AS_DEFAULT:
        ctr = JoystickController(max_throttle=cfg.JOYSTICK_MAX_THROTTLE,
                                 steering_scale=cfg.JOYSTICK_STEERING_SCALE,
                                 auto_record_on_throttle=cfg.AUTO_RECORD_ON_THROTTLE)
    else:
        # This web controller will create a web server that is capable
        # of managing steering, throttle, and modes, and more.
        ctr = LocalWebController(use_chaos=use_chaos)

    V.add(ctr,
          inputs=['cam/image_array'],
          outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
          threaded=True)

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True

    pilot_condition_part = Lambda(pilot_condition)
    V.add(pilot_condition_part, inputs=['user/mode'],
          outputs=['run_pilot'])

    # Run the pilot if the mode is not user.
    kl = KerasCategorical()
    if model_path:
        kl.load(model_path)

    V.add(kl, inputs=['cam/image_array'],
          outputs=['pilot/angle', 'pilot/throttle'],
          run_condition='run_pilot')

    # Choose what inputs should change the car.
    def drive_mode(mode,
                   user_angle, user_throttle,
                   pilot_angle, pilot_throttle):
        if mode == 'user':
            return user_angle, user_throttle

        elif mode == 'local_angle':
            return pilot_angle, user_throttle

        else:
            return pilot_angle, pilot_throttle

    drive_mode_part = Lambda(drive_mode)
    V.add(drive_mode_part,
          inputs=['user/mode', 'user/angle', 'user/throttle',
                  'pilot/angle', 'pilot/throttle'],
          outputs=['angle', 'throttle'])

    steering_controller = PCA9685(cfg.STEERING_CHANNEL)
    steering = PWMSteering(controller=steering_controller,
                           left_pulse=cfg.STEERING_LEFT_PWM,
                           right_pulse=cfg.STEERING_RIGHT_PWM)

    throttle_controller = PCA9685(cfg.THROTTLE_CHANNEL)
    throttle = PWMThrottle(controller=throttle_controller,
                           max_pulse=cfg.THROTTLE_FORWARD_PWM,
                           zero_pulse=cfg.THROTTLE_STOPPED_PWM,
                           min_pulse=cfg.THROTTLE_REVERSE_PWM)

    V.add(steering, inputs=['angle'])
    V.add(throttle, inputs=['throttle'])

    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'timestamp']
    types = ['image_array', 'float', 'float', 'str', 'str']

    # multiple tubs
    # th = TubHandler(path=cfg.DATA_PATH)
    # tub = th.new_tub_writer(inputs=inputs, types=types)

    # single tub
    tub = TubWriter(path=cfg.TUB_PATH, inputs=inputs, types=types)
    V.add(tub, inputs=inputs, run_condition='recording')

    # run the vehicle
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)

def load_image(path):
    img = Image.open(path)
    return np.array(img)

def get_generator(input_keys, output_keys, record_paths, meta, tub_path):
    while True:
        for record_path in record_paths:
            with open(record_path, 'r') as record_file:
                record = json.load(record_file)
                inputs = [record[key] for key in input_keys]
                outputs = [record[key] for key in output_keys]
                input_types = [meta[key] for key in input_keys]
                # output_types = [meta[key] for key in output_keys]
                for i in range(len(inputs)):
                    type = input_types[i]
                    if (type == 'image_array'):
                        inputs[i] = load_image("%s/%s" % (tub_path, inputs[i]))
                    elif (type == 'custom/prev_image'):
                        # Currently previous images are in array, but there is only one
                        imagePath = inputs[i][0]
                        inputs[i] = load_image("%s/%s" % (tub_path, imagePath))
                yield inputs, outputs

def get_batch_generator(input_keys, output_keys, records, meta, tub_path):
    # Yield here a tuple (inputs, outputs)
    # both having arrays with batch_size length like:
    # 0: [input_1[batch_size],input_2[batch_size]]
    # 1: [output_1[batch_size],output_2[batch_size]]
    record_gen = get_generator(input_keys, output_keys, records, meta, tub_path)
    while True:
        raw_batch = [next(record_gen) for _ in range(cfg.BATCH_SIZE)]
        inputs = [[] for _ in range(len(input_keys))]
        outputs = [[] for _ in range(len(output_keys))]
        for rec in raw_batch:
            for i in range(len(input_keys)):
                inputs[i].append(rec[0][i])
            for i in range(len(output_keys)):
                outputs[i].append(rec[1][i])
        numpyInputs = [np.asarray(ar) for ar in inputs]
        numpyOutputs = [np.asarray(ar) for ar in outputs]
        yield numpyInputs, numpyOutputs

def get_meta(path):
    with open('%s/meta.json' % path, 'r') as f:
        meta = json.load(f)
        meta_dict = {}
        for i, key in enumerate(meta['inputs']):
            meta_dict[key] = meta['types'][i]
        return meta_dict
            # TODO: filter out values not listed in inputs or outputs


def get_train_val_gen(inputs, outputs, tub_names):
    print('Loading data', tub_names)
    print('Inputs', inputs)
    print('Outputs', outputs)
    tubs = glob.glob('%s' % tub_names)
    for tub in tubs:
        print(tub)
        meta = get_meta(tub)
        print(meta)
        # TODO: Check if meta.json specs match with given inputs and outputs
        record_files = glob.glob('%s/record*.json' % tub)
        np.random.shuffle(record_files)
        split = int(round(len(record_files) * cfg.TRAIN_TEST_SPLIT))
        train_files, validation_files = record_files[:split], record_files[split:]
    return get_batch_generator(inputs, outputs, train_files, meta, tub), get_batch_generator(inputs, outputs, validation_files, meta, tub), len(record_files)

def train(cfg, tub_names, new_model_path, base_model_path=None):
    """
    use the specified data in tub_names to train an artifical neural network
    saves the output trained model as model_name
    """
    inputs = ['cam/image_array', 'cam/prev_images', 'history/angle', 'history/throttle']
    outputs = ['user/angle', 'user/throttle']

    new_model_path = os.path.expanduser(new_model_path)

    kl = CustomModel()
    # Load base model if given
    if base_model_path is not None:
        base_model_path = os.path.expanduser(base_model_path)
        kl.load(base_model_path)

    # Support for multiple paths
    print('tub_names', tub_names)
    if not tub_names:
        tub_names = os.path.join(cfg.DATA_PATH, '*')
    else:
        print('No support for custom tubs yet')
        exit(0)

    train_gen, val_gen, total_train = get_train_val_gen(inputs, outputs, tub_names)

    #tubgroup = TubGroup(tub_names)
    # orig_train_gen, orig_val_gen = tubgroup.get_train_val_gen(inputs, outputs,
    #                                                 batch_size=cfg.BATCH_SIZE,
    #                                                 train_frac=cfg.TRAIN_TEST_SPLIT)


    # Testing the batch generation
    # for i in range(5):
    #     new_batch = next(train_gen)
        # orig_batch = next(orig_train_gen)
        # print('Tick')
    # total_records = len(tubgroup.df)
    # total_train = int(total_records * cfg.TRAIN_TEST_SPLIT)

    steps_per_epoch = total_train // cfg.BATCH_SIZE

    kl.train(train_gen,
             val_gen,
             saved_model_path=new_model_path,
             steps=steps_per_epoch,
             train_split=cfg.TRAIN_TEST_SPLIT)


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = dk.load_config()

    if args['drive']:
        drive(cfg, model_path=args['--model'], use_joystick=args['--js'], use_chaos=args['--chaos'])

    elif args['train']:
        tub = args['--tub']
        new_model_path = args['--model']
        base_model_path = args['--base_model']
        cache = not args['--no_cache']
        train(cfg, tub, new_model_path, base_model_path)
