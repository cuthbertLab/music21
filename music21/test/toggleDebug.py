import music21.environment

if __name__ == '__main__':
    e = music21.environment.UserSettings()
    if e['debug'] == 1:
        print 'debug was ' + str(e['debug']) + '; switching to 0'
        e['debug'] = 0
    else:
        print 'debug was ' + str(e['debug']) + '; switching to 1'
        e['debug'] = 1