#!/bin/sh


# Get the postgresql-9.6.2 source file 
wget https://ftp.postgresql.org/pub/source/v9.6.2/postgresql-9.6.2.tar.gz

gunzip postgresql-9.6.2.tar.gz
tar xf postgresql-9.6.2.tar

cd /home/vagrant/postgresql-9.6.2

# Configuration
./configure

# Build
make

#Installing the files
make install

#Cleaning
make clean