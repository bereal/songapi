import fileinput
import json

# Convert the original test data to valid json

def main():
    data = []
    for line in fileinput.input():
        data.append(json.loads(line))

    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
