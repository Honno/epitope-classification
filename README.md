# Data mining for Linear B-cell Epitopes

This repository pertains to my *CS3440 Data Mining* university coursework
submission, where we were tasked to explore a [dataset](CW_Data_train.arff) and
devise a performant [Weka](https://www.cs.waikato.ac.nz/~ml/weka/) model for it.
My final report is available at [report.pdf](report.pdf) :)

In particular, I am proud of the preprocessing strategy devised. After noticing
a strange pattern in the data—where duplicate records contained slightly
different values that obscured basic duplicate analysis tools—I wrote a bespoke
Python script to generate [analysis](./preprocess/distribution.csv) and
ultimately reduce duplicate records, available at
[preprocess/preprocess_data.py](./preprocess/preprocess_data.py), and is
detailed in the report at section 4.2 *Duplicate reduction*.
