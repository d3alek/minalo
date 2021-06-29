#!venv/bin/python3
# Как да събираме промените - крайните потребители могат да публикуват клонове на публичното репо от съучастници. Репо-то избира дали да приеме клона по това дали комита минава проверките. Клона следва да е с име <публичен-ключ-на-променящия>-<минута>

# Значи архитектурата е:
# имаме съучастници със гит адреси
# имаме хора които правят промени, които трябва да имат ключ - с този ключ им се позволява да правят промени
# Използвам приложението Termux и https://wiki.termux.com/wiki/Remote_Access тези инструкции. При грешка git remote HEAD refers to nonexistent ref: cd path/to/git/repo; git symbolic-ref HEAD refs/heads/main
# Първоначално съучастниците (на всякаква линукс конзола, включително андроид телефони) теглят от zhiva.be/minalo последното репо (с wget например) правят install.sh (TODO)
# pip install virtualenv
# Правят virtualenv venv
# source venv/bin/activate
# pip install -r requirements.txt
# После стартират python минало.py

# Разделяме минутата на части
# Половината от минутата само слушаме
# 

import datetime
import time
from sh import git

СЛУШАНЕ = 30
СГЛОБЯВАНЕ = 35
ПУБЛИКУВАНЕ = 40
РАЗГЛЕЖДАНЕ = 45
ПРЕДЛАГАНЕ = 50
ПРИЕМАНЕ = 60

def now():
    return datetime.datetime.now()

def минута():
    while True:
        print(now(), 'Слушам')
        # Хора пращат промени към нас или други съучастници. Те са в клонове с публичен ключ на изпращащия и минутата за която се отнасят. Така автоматично един изпращащ не може да публикува две промени за една минута
        # https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
        # Използваме pre-recieve hook за да приемаме само клони които отговарят на правилата
        # Използваме post-recieve hook за да известим питонския скрипт за получените промени
        # Използваме pre-commit hook за да наложим правила
        time.sleep(max(0, СЛУШАНЕ - now().second))

        print(now(), 'Сглобявам минута')
        # От получените събития правим минута (блок), като наслагваме всички върху миналата минута.

        time.sleep(max(0, СГЛОБЯВАНЕ - now().second))

        print(now(), 'Публикувам минута')
        # Публикуваме нашата минута в клон <минута>

        time.sleep(max(0, ПУБЛИКУВАНЕ - now().second))

        print(now(), 'Разглеждам минути')
        # Проверяваме минутите на другите съучастници - ако имат различни промени от нашата, нанасяме допълнителните промени към нашите.

        time.sleep(max(0, РАЗГЛЕЖДАНЕ - now().second))

        print(now(), 'Предлагам минута')
        # Предлагаме нашата най-добра минута на водачите за тази минута. Той се определя на някакъв глобален принцип на базата на мястото му в съучастници. Ако няма връзка с него, предлагаме на първия след него с когото има връзка TODO Може да имаме 3ма водачи?
        # Водачите избират предложението с най-много промени.

        time.sleep(max(0, ПРЕДЛАГАНЕ - now().second))

        print(now(), 'Приемам минута')

        # Приемаме състоянието на водача (водачите). Ако имаме локални комити които не са влезли в приетото състояние, запазваме ги за следващата минута. Изчистваме всички клони за миналата минута.

        time.sleep(max(0, ПРИЕМАНЕ - now().second))

# Ако имаме 33ма съучастници, на базата на коя минута от деня е, делим на броя на участниците и взимаме остатъка от деленето - този и следващите двама участника са водачи. На тях може да се пращат новите комити.

# Промени в кода се приемат само с няколко (3) подписа на разработчици (такива които са правили вече промени по кода).

if __name__ == '__main__':
    минута()
