# Минало

## Създаване на минута на ръка

```
date -Iminute -u | cut -f1 -d'+' | sed 's/:/-/' > време
git checkout -b $(cat време)
git add време
git commit -am "Минута $(cat време)"
```

