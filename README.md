# Минало

## Създаване на минута на ръка

```
date -Iminute -u | cut -f1 -d'+' | sed 's/:/-/' > време
git checkout -b $(cat време)
git add време
git commit -am "Минута $(cat време)"
```

Това правят двамата съучастници. След което дърпат клона с това име от другите съучастници. 

```
git fetch minalo2 $(cat време)
DIFF=$(git diff --exit-code minalo2/$(cat време) време)
[ $DIFF -eq 0 ] && echo 'Accept' || echo 'Reject'
```


