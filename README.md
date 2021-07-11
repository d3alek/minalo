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
cd minalo
export GNUPGHOME=$(pwd)/тайник
mkdir GNUPGHOME
gpg --quick-generate-key # или gpg --gen-key ако това го няма
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

## Как да се свързваме въпреки променливи IPта и NAT

Участник с променливо IP и/или зад NAT (така че SSH към публичния IP не стига до него). Нещо като https://blog.kokanovic.org/access-ssh-behind-nat/ . Ето го питонския начин: https://github.com/paramiko/paramiko/blob/master/demos/rforward.py

Нужен ни е публичен сървър. Изкушавам се от EC2 сървърче безплатно за година.
