ZHIVABE=/home/alek/zhiva-mrezha/zhiva-mrezha.github.io/static
TIME=$(cat време)
tar -zcvf $ZHIVABE/minalo.tar.gz --exclude-from='exclude' .
cd $ZHIVABE
git add minalo.tar.gz
git commit -am "Автоматично публикувано Минало $TIME".
git push
