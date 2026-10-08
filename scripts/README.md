# Scripts

Thin wrappers only; logic lives in the `fabric_foundry_accelerator` package (`ffia` CLI).

One exception: `verify_spark_notebooks.py` runs the committed Fabric reference notebooks on a local
Apache Spark 3.5 session (the engine of Fabric Runtime 1.3). It needs PySpark 3.5 and Java 17, which
are deliberately not project dependencies, so it is a standalone development-time check:

```bash
JAVA_HOME=<jdk-17> <python-with-pyspark-3.5.9> scripts/verify_spark_notebooks.py
```

Its result is LOCAL evidence that the notebook code and SQL run on Spark 3.5. It is not evidence
that anything ran in Fabric.
