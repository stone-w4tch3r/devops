#!/bin/bash

multipass delete primary
multipass purge
multipass launch --name primary --disk 15G focal