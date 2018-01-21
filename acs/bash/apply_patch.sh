#!/usr/bin/env bash
cd $1
git -c user.name='CheckiePyBot' -c user.email='bot@checkiepy.com' am --signoff < $2
