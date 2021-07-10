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
$DIFF && echo 'Accept' || echo 'Reject'
```

## Настройка на нов телефон

```
git clone https://github.com/d3alek/minalo.git
pkg install gnupg
```
