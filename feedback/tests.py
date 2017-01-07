from django.test import TestCase

# Create your tests here.
a = [1,2,3,4,5,6,7,8,9,0,-1]
n=11
m=3
for i in range(0, n+1, m):  #i=i+m
    for j in range(m+i,i,-1):
        if j >= n: break
        print(a[j-1])
for i in range(n-1, n-n%m-1, -1):
    print(a[i])