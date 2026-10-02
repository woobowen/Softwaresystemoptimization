# 验证生成器修改时的失败

计时适配后去除生产源码行尾空格，原唯一 `return 0` 替换marker变成与新插入参考函数中的同名返回匹配两次。small及sanitizer生成均触发 `AssertionError: Unexpected source marker: '    return 0;'`，尚未编译/运行。保留两份头记录为 validation-marker-failed-*.jsonl。修正为在插入参考函数前检查并替换生产函数返回；同源循环比较仍在所有替换前后各做一次。接着重跑相关套件。
