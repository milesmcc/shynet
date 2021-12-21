# Contributing

This document provides an overview of how to contribute to Shynet. Currently, it focuses on the more technical elements of contributing --- for example, setting up your development environment. Eventually, we will expand this guide to cover the social and governance oriented side of contributing as well.

## Setting up your development environment

To contribute to Shynet, you must have a reliable development environment. Because Shynet is intended to be run inside containers, we strongly encourage you to run Shynet in a container in development as well. The development setup described in this guide will use Docker and Docker Compose.

To begin, clone the Shynet repository to your computer, and ensure that you have Docker and Docker Compose installed.

Copy `TEMPLATE.env` to a new file called `.env`. This `.env` file will be used in your development environment. Paste `DEBUG=True` into the end of your new `.env` file so that Shynet will know to run in development mode.

Finally, follow the steps in [GUIDE.md](GUIDE.md) on setting up a Shynet instance with Docker Compose. This is where you'll setup an admin user.

_Did you have to perform additional steps to setup your environment? Document them here and submit a pull request!_