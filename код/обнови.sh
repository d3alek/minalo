DIR=$(dirname "$0")
wget https://zhiva.be/minalo.tar.gz
rm -fr $DIR/ново-минало
mkdir $DIR/ново-минало
tar -xvf ../minalo.tar.gz -C $DIR/ново-минало
git remote add update $DIR/ново-минало
git pull update main
