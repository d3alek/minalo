from sh import git, cat, wget

време = cat('време').strip()
промени = int(git('rev-list', време, '--count'))
кандидат_клон = 'кандидат-' + време

for съучастник in git.remote().split():
    try:
        git.fetch(съучастник, време)
    except:
        print("Не намерих", време, "при", съучастник)
        continue
    клон = съучастник+'/'+време
    try:
        git.diff('--exit-code', клон, 'време')
        print('Приемам', време, съучастник)
    except:
        print("Отхвърлям", време, съучастник)
        continue

    промени2=int(git('rev-list', клон, '--count'))
    if промени > промени2:
        print("Избирам моята минута пред тази на", съучастник)
        git.branch('-C', време, кандидат_клон)
    else:
        print("Избирам минутата на", съучастник)
        git.branch('-f', кандидат_клон, клон)
