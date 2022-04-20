# Rally Dreamer

> A MDN-RNN model built to learn a rally game (DiRT Rally), with a visual encoder

A rally driving machine learning application inspired by the article [World Models](https://worldmodels.github.io/).

This application is composed of a Variational Autoencoder (VAE) that takes in images from a rally game and encodes it into a latent vector `z_(t-1)`. This vector is fed into a Recurrent Neural Network (RNN) along with history data `h_(t-1)` and actions `a_(t-1)`. The RNN will then yield a density function of the future `z_t` denoted as `p(z)`, and new history item `h_t`. A Mixture Density Network (MDN) is used to convert the density function `p(z)` into an estimation of the future `z_t`.

This project is meant to support any rally game, so long as it runs on Windows and can provide telemetry data to a 3rd party application. However, the main focus of the development has been to make the project support DiRT Rally in particular.

## Requirements

- PyCharm
- Python 3.8

## Literature

- [Auto-Encoders for Computer Vision: An Endless world of Possibilities](https://www.analyticsvidhya.com/blog/2021/01/auto-encoders-for-computer-vision-an-endless-world-of-possibilities/)
- [Mixture Density Networks](https://publications.aston.ac.uk/id/eprint/373/1/NCRG_94_004.pdf)
- [Recurrent neural network (Wikipedia)](https://en.wikipedia.org/wiki/Recurrent_neural_network)
- [Variational Autoencoder (Wikipedia)](https://en.wikipedia.org/wiki/Variational_autoencoder)
