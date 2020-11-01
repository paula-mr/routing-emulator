from math import inf
def main():
    links = {
        '127.0.1.1': 
        {
            '127.0.1.1': 0, 
            '127.0.1.2': 1,
            # '127.0.1.3': 3
        }, 
        '127.0.1.2':
        {
            '127.0.1.1': 1,
            '127.0.1.2': 0,
            # '127.0.1.3': 2#
        },
        '127.0.1.3':
        {
            '127.0.1.1': 3,
            '127.0.1.2': 2,
            # '127.0.1.3': 10
        }
    }

    ip = '127.0.1.3'
    a = min(filter(lambda x: x is not None, map(lambda dic: dic.get(ip, None), links.values())), default=inf)
    print(a)

main()