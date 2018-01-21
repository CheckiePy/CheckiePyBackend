#!/bin/bash
gunicorn acs.wsgi --workers 3 --bind=unix:./run/gunicorn.sock