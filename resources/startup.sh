#!/bin/bash

faststream run src.main:app --workers $(python3 src/scripts/get_workers_amount.py)