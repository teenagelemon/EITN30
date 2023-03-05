import matplotlib.pyplot as plt

f = open("result.txt", "r")
f.readline()
line = f.readline().split("=")

numbers = []
i = 0
while i < 10:
    number = line[-1].split(" ")[0]
    numbers.append(float(number))
    line = f.readline().split("=")
    i += 1

print(numbers)
f.close()


plt.rcParams["figure.figsize"] = [10, 10]
plt.rcParams["figure.autolayout"] = True

x = range(len(numbers))

plt.title("Line graph")
plt.plot(x, numbers, color="red")

plt.show()
