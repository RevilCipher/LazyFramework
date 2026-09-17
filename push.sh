#!/bin/bash

git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/RevilCipher/LazyFramework.git
git push -u -f origin main
