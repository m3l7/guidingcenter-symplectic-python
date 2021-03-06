#!/bin/sh
DATE=$(date +"%Y-%m-%d_%H:%M:%S")
SIM_PREFIX="sims"
GITTOKEN=$(git rev-parse HEAD | cut -c1-10)
SIM_FOLDER="$DATE"_$GITTOKEN
FOLDERPREFIX=$SIM_PREFIX/"$SIM_FOLDER"

mkdir -p $FOLDERPREFIX/out
mkdir -p $FOLDERPREFIX/src
mkdir -p $FOLDERPREFIX/plots
mkdir -p plots
mkdir -p out
cd $SIM_PREFIX
rm last
ln -s $SIM_FOLDER last
cd ..

echo "=== Backing up sources"
cp -r src/* $FOLDERPREFIX/src

echo "=== Starting simulation: saving to $FOLDERPREFIX"
echo "begin simulation "$DATE > $FOLDERPREFIX/info.txt
script -q -c "python3 src/main.py -o $FOLDERPREFIX/out/out.txt" /dev/null | tee $FOLDERPREFIX/info.txt
echo "end simulation "$(date +"%Y-%m-%d_%H:%M:%S") >> $FOLDERPREFIX/info.txt
echo "=== End simulation"

echo "Creating symbolic link of data and charts"
cd out
rm out.txt
ln -s ../"$FOLDERPREFIX"/out/out.txt .
cd ..

# save plots
echo "=== Saving charts"
python3 src/plot.py --folderprefix=plots/ --date="$DATE"_ -i out/out.txt
cp plots/last_* $FOLDERPREFIX/plots/

# if [ -f "Blines.txt" ]
# then
# 	mv Blines.txt $SIM_PREFIX/$1/
# fi
