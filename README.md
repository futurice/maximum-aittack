# maximum-aittack
Utilities for autonomous driving. Based on donkeycar autonomous RC-car project

### Digital racing with supervised learning

#### Recording your laps
Recording the training includes saving screencaps and corresponding controller values (throttle and steering axes).

1. Activate conda env with `conda activate aicontrol`
1. Start the game and load the level (Preferably in windowed mode maximized)
1. Start the recording script with `python record.py --name=someidentifier` 
1. Alt-tab to game and wait for windows bell sound stating the recording started
1. Drive around
1. If you hear three bell sounds, either max datapoints reached or something went wrong and there was an exception
1. Trim possible bad data from the beginning and end of the recorded data under `logs/someidentifier`
1. GOTO 1 or if enough data, start training

#### Training the model
Training takes your test data in and saves a model file to use for driving.

1. Copy the recorder data directory under `car-beamng/data`
1. Activate conda env with `conda activate donkey` 
1. Run `python manage.py train --model=models/somemodel`
    1. You can follow the training with tensorboard by running `tensorboard --logdir Graph` and opening tensorboard url in browser
    1. You can also use another model as a base with `--base_model=models/othermodel`
1. Wait for the training to finish
1. Your trained model can be found under `/models`

#### Driving
Letting the AI behind the wheel means that a script starts taking screencaps and feeding them into the trained neural network model.
Neural network then returns throttle and steering value, which in turn are pushed through a virtual joystick.

1. Activate conda env with `conda activate donkey-cpu` (or `conda activate donkey` if two GPUs available)
1 .Start the game and ensure vJoy axes are mapped to throttle and steering
    1. Helpers for mapping the controls can be used with `python joystick.py throttle` and `python joystick.py steering`
1. Load level and leave the car waiting. Again best guess is windowed and maximized.
1. Start the simulation with `python joystick drive --model=models/somemodel`
1. If you kill the simulation and need to reset vJoy axes, run `python joystick reset`
1. Now maximum aittack
