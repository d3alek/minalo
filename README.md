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
mkdir $GNUPGHOME
gpg --quick-generate-key user-id # нужен е gpg версия >=2.2
ssh-keygen
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

## Как да се свързваме въпреки променливи IPта и NAT

Участник с променливо IP и/или зад NAT (така че SSH към публичния IP не стига до него). Нещо като https://blog.kokanovic.org/access-ssh-behind-nat/ . Ето го питонския начин: https://github.com/paramiko/paramiko/blob/master/demos/rforward.py

Нужен ни е публичен сървър. Изкушавам се от EC2 сървърче безплатно за година.

```
ssh -fN -R 10022:localhost:22 ubuntu@3.122.41.243
```

И после:

```
ssh alek@3.122.41.243 -p 10022
# или
python rforward.py 3.122.41.243 -r localhost -p 10022 -u ubuntu
```

Въпреки че localhost няма реално IP.

## Git настройки
```
git config core.quotepath off
git config commit.gpgsign true
git config user.signingkey <key>
```

```
.ssh/config
---
Host *
   StrictHostKeyChecking no
   UserKnownHostsFile=/dev/null
   LogLevel QUIET 
   ConnectTimeout 1
```

Ако някой се включи, но не е в час (в минута по-скоро), не знае кой е водача. Тоест, ако знае коя е минутата и ако има правилните съучастници, може да познае, но... Затова да тегли main от няколко (да кажем 3) съучастника и ако всички са различни - кофти, избухни, но ако поне две са еднакви, ползвай него. Като за начало тегли само от един и се хвани за неговата верига.
