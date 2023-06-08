# ugit_learn

ugit learn

[ugit: DIY Git in Python](https://www.leshenko.net/p/ugit/#)

## .ugit

这个文件夹存放所有信息

- HEAD

文件

保存当前所在分支或者提交

- refs/tags

文件夹

存放标签 tag

- refs/heads

文件夹

存放分支

- objects

文件夹

存放对象，类型如下

blob 保存的是文件内容

commit 保存提交信息

tree 保存文件夹信息

## 想法

一开始以为 git 每次提交记录的是变更的内容，

看了这个之后发现，原来每次都是保存的快照，

只不过每次提交保存的都是变更的文件，没有变更的文件不需要再保存一份。

整个系列文章层层递进，聚焦于核心逻辑，非常容易理解和学习，这才是真正的教程。

不会跟你长篇大论地讨论各种概念和名词，说实话，讨论这些就落入圈套，会把自己脑子弄得一团槽。
