#!/usr/bin/env bash
cd $1
git -c user.name='acsproj bot' -c user.email='bot@acsproj.com' am --signoff < p.patch
