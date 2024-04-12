#!/bin/bash

export CUDA_VISIBLE_DEVICES=1
torchrun --nproc_per_node 1 agent.py
