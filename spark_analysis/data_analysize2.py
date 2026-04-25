# -*- coding: utf-8 -*-
"""
BÕ¾¡¶Ã¿ÖÜ±Ø¿´¡·ÊÓÆµÓëupÖ÷Êý¾ÝµÄ´óÊý¾Ý·ÖÎöÈÎÎñ - ÈÎÎñ3
Ê¹ÓÃSpark MLlib½øÐÐ»úÆ÷Ñ§Ï°·ÖÀàÔ¤²â
"""

import os
import pandas as pd

# ÅäÖÃÐÅÏ¢
INPUT_PATH = "./dataset/bilibili.txt"
OUTPUT_DIR = "./output"
STATIC_DIR = "./static"

# È·±£Êä³öÄ¿Â¼´æÔÚ
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# ³õÊ¼»¯Spark²¢¼ÓÔØÊý¾Ý
def initialize(txt_file):
    """
    ³õÊ¼»¯Spark²¢¼ÓÔØÊý¾Ý
    """
    from pyspark import SparkContext
    from pyspark.sql import SparkSession, Row
    
    spark = SparkSession.builder \
        .appName("Bilibili ML Prediction") \
        .getOrCreate()
    
    # ½âÎöÊý¾ÝÐÐ
    def parse_line(line):
        parts = line.split('\t')
        if len(parts) < 15:
            return None
        try:
            return Row(
                up_name=parts[0],
                week_name=parts[1],
                title=parts[2],
                description=parts[3],
                view=int(parts[4]),
                danmaku=int(parts[5]),
                reply=int(parts[6]),
                favorite=int(parts[7]),
                coin=int(parts[8]),
                share=int(parts[9]),
                like=int(parts[10]),
                rcmd_reason=parts[11],
                tname=parts[12],
                his_rank=int(parts[13]),
                label=int(parts[14])
            )
        except:
            return None
    
    # ¼ÓÔØ²¢´¦ÀíÊý¾Ý
    rdd = spark.sparkContext.textFile(txt_file) \
        .map(parse_line) \
        .filter(lambda x: x is not None)
    
    data = spark.createDataFrame(rdd)
    return data

# Êý¾Ý×ª»»ºÍÌØÕ÷¹¤³Ì
def transform_data(df):
    """
    Êý¾Ý×ª»»ºÍÌØÕ÷¹¤³Ì
    """
    from pyspark.sql.functions import col, round
    from pyspark.ml.feature import VectorAssembler
    
    # ¼ÆËã»¥¶¯ÂÊµÈÑÜÉúÌØÕ÷
    df = df.withColumn('interact_rate', \
                       round((col('like') + col('coin') + col('favorite') + col('share') + col('reply')) / col('view'), 4))
    df = df.withColumn('like_rate', round(col('like') / col('view'), 4))
    df = df.withColumn('coin_rate', round(col('coin') / col('view'), 4))
    
    # Ñ¡ÔñÌØÕ÷ÁÐ
    required_features = ['view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like', 'interact_rate', 'like_rate', 'coin_rate']
    
    # ¹¹½¨ÌØÕ÷ÏòÁ¿
    assembler = VectorAssembler(
        inputCols=required_features,
        outputCol='features')
    transformed_data = assembler.transform(df)
    
    # »®·ÖÑµÁ·¼¯ºÍ²âÊÔ¼¯
    (training_data, test_data) = transformed_data.randomSplit([0.8, 0.2], seed=2023)
    print("Training data count: " + str(training_data.count()))
    print("Test data count: " + str(test_data.count()))
    
    return transformed_data, training_data, test_data

# ¼ÆËãÏà¹ØÐÔ¾ØÕó
def corr_matrix(df, cor_save_dir):
    """
    ¼ÆËãÏà¹ØÐÔ¾ØÕó
    """
    from pyspark.ml.stat import Correlation
    
    cor_mat = Correlation.corr(df, "features", "spearman").head()[0]
    cor_df = pd.DataFrame(cor_mat.toArray())
    cor_df.columns = ['view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like', 'interact_rate', 'like_rate', 'coin_rate']
    ensure_dir(os.path.dirname(cor_save_dir))
    cor_df.to_csv(cor_save_dir, index=False)
    print(f"Ïà¹ØÐÔ¾ØÕóÒÑ±£´æµ½ {cor_save_dir}")

# Âß¼­»Ø¹éÄ£ÐÍ
def LogisticReg(training_data, test_data):
    """
    Âß¼­»Ø¹éÄ£ÐÍ
    """
    from pyspark.ml.classification import LogisticRegression
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    
    lr = LogisticRegression(labelCol='label', featuresCol='features', maxIter=15)
    model = lr.fit(training_data)
    lr_predictions = model.transform(test_data)
    
    # ¼ÆËã×¼È·ÂÊ
    multi_evaluator = MulticlassClassificationEvaluator(
        labelCol='label', metricName='accuracy')
    acc = multi_evaluator.evaluate(lr_predictions)
    print('LogisticRegression classifier Accuracy:{:.4f}'.format(acc))
    
    # ¼ÆËãAUC
    binary_evaluator = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction", labelCol="label",
        metricName="areaUnderROC")
    auc = binary_evaluator.evaluate(lr_predictions)
    print('LogisticRegression classifier Auc:{:.4f}'.format(auc))
    
    return ['LogisticRegression', acc, auc]

# ¾ö²ßÊ÷Ä£ÐÍ
def DecisionTree(training_data, test_data):
    """
    ¾ö²ßÊ÷Ä£ÐÍ
    """
    from pyspark.ml.classification import DecisionTreeClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    
    dt = DecisionTreeClassifier(labelCol='label',
                                featuresCol='features',
                                maxDepth=5)
    model = dt.fit(training_data)
    dt_predictions = model.transform(test_data)
    
    # ¼ÆËã×¼È·ÂÊ
    multi_evaluator = MulticlassClassificationEvaluator(
        labelCol='label', metricName='accuracy')
    acc = multi_evaluator.evaluate(dt_predictions)
    print('DecisionTree classifier Accuracy:{:.4f}'.format(acc))
    
    # ¼ÆËãAUC
    binary_evaluator = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction", labelCol="label",
        metricName="areaUnderROC")
    auc = binary_evaluator.evaluate(dt_predictions)
    print('DecisionTree classifier Auc:{:.4f}'.format(auc))
    
    return ['DecisionTree', acc, auc]

# Ëæ»úÉ­ÁÖÄ£ÐÍ
def Randomforest(training_data, test_data):
    """
    Ëæ»úÉ­ÁÖÄ£ÐÍ
    """
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    
    rf = RandomForestClassifier(labelCol='label',
                                featuresCol='features',
                                maxDepth=5)
    model = rf.fit(training_data)
    rf_predictions = model.transform(test_data)
    
    # ¼ÆËã×¼È·ÂÊ
    multi_evaluator = MulticlassClassificationEvaluator(
        labelCol='label', metricName='accuracy')
    acc = multi_evaluator.evaluate(rf_predictions)
    print('Random Forest classifier Accuracy:{:.4f}'.format(acc))
    
    # ¼ÆËãAUC
    binary_evaluator = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction", labelCol="label",
        metricName="areaUnderROC")
    auc = binary_evaluator.evaluate(rf_predictions)
    print('Random Forest classifier Auc:{:.4f}'.format(auc))
    
    return ['Random Forest', acc, auc]

# GBTÄ£ÐÍ
def GBT(training_data, test_data):
    """
    GBTÄ£ÐÍ
    """
    from pyspark.ml.classification import GBTClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    
    gb = GBTClassifier(labelCol='label', featuresCol='features', maxDepth=5)
    model = gb.fit(training_data)
    gb_predictions = model.transform(test_data)
    
    # ¼ÆËã×¼È·ÂÊ
    multi_evaluator = MulticlassClassificationEvaluator(labelCol='label', metricName='accuracy')
    acc = multi_evaluator.evaluate(gb_predictions)
    print('GBT classifier Accuracy:{:.4f}'.format(acc))
    
    # ¼ÆËãAUC
    binary_evaluator = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction", labelCol="label",
        metricName="areaUnderROC")
    auc = binary_evaluator.evaluate(gb_predictions)
    print('GBT classifier Auc:{:.4f}'.format(auc))
    
    return ['GBT', acc, auc]

# ÑµÁ·ºÍÆÀ¹ÀÄ£ÐÍ
def train(df, cor_dir, classifier_comparison_dir):
    """
    ÑµÁ·ºÍÆÀ¹ÀÄ£ÐÍ
    """
    transformed_data, training_data, test_data = transform_data(df)
    
    # ¼ÆËã±äÁ¿Ö®¼äµÄÏà¹ØÐÔ
    corr_matrix(transformed_data, cor_dir)
    
    # Ê¹ÓÃËÄÖÖ·ÖÀàÆ÷½øÐÐ·ÖÀà
    log_res = LogisticReg(training_data, test_data)
    dt_res = DecisionTree(training_data, test_data)
    rf_res = Randomforest(training_data, test_data)
    gbt_res = GBT(training_data, test_data)
    
    # ½«·ÖÀàÆ÷µÄÐÔÄÜ½á¹û±£´æÔÚcsvÎÄ¼þÖÐ
    classifier_comparison = [log_res, dt_res, rf_res, gbt_res]
    comparison_df = pd.DataFrame(classifier_comparison)
    comparison_df.columns = ['classifier', 'Acc', 'Auc']
    ensure_dir(os.path.dirname(classifier_comparison_dir))
    comparison_df.to_csv(classifier_comparison_dir, index=False)
    print(f"·ÖÀàÆ÷ÐÔÄÜ½á¹ûÒÑ±£´æµ½ {classifier_comparison_dir}")

if __name__ == '__main__':
    print("BÕ¾¡¶Ã¿ÖÜ±Ø¿´¡·ÊÓÆµÓëupÖ÷Êý¾ÝµÄ´óÊý¾Ý·ÖÎöÈÎÎñ - ÈÎÎñ3")
    print("Ê¹ÓÃSpark MLlib½øÐÐ»úÆ÷Ñ§Ï°·ÖÀàÔ¤²â")
    
    # ¼ÓÔØÊý¾Ý
    df = initialize(INPUT_PATH)
    print(f"Êý¾Ý¼ÓÔØÍê³É£¬¹² {df.count()} Ìõ¼ÇÂ¼")
    
    # ¶¨ÒåÊä³öÂ·¾¶
    cor_save = os.path.join(STATIC_DIR, 'cor_matrix.csv')
    classifier_comparison_dir = os.path.join(STATIC_DIR, 'comparison.csv')
    
    # ÑµÁ·Ä£ÐÍ
    train(df, cor_save, classifier_comparison_dir)
    
    print("ÈÎÎñ3Íê³É£ºÊ¹ÓÃSpark MLlib½øÐÐ»úÆ÷Ñ§Ï°·ÖÀàÔ¤²â")
