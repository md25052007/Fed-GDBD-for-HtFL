Fed-GDBD for Heterogeneous Federated Learning - project submission
IT307 Machine Learning, NIT Karnataka, Surathkal

Authors: D Maithreya, Maharshi Kundu, Siddhanth R Naik, Rufsina A, Nagamma Patil
GitHub:  https://github.com/md25052007/Fed-GDBD-for-HtFL

1_Source_Code
    Fed-GDBD-for-HtFL.zip   The code, at the submitted commit:
                              system/       training code (HtFLlib + Fed-GDBD, FedGDBD-S, AGC, AGS)
                              dataset/      scripts that build the 20-client split
                              scripts/      run and progress-check scripts (Windows)
                              analysis/     scripts that make every number, table and figure
                              experiments/  logs and result files of every run (read by analysis/)
                              setup.bat, requirements.txt
                            Start with README.md, then REPRODUCTION.md for every run step by step.
                            The paper, report and slides (docs/ in the GitHub repo) are in
                            3_Paper and 4_Additional instead.

2_Dataset
    DATASET.md              Which datasets we used, where to get them, and exactly how they
                            were split over the 20 clients.
    split_scripts/          The generator scripts that make the split.
    Cifar10_config.json,
    Cifar100_config.json    Number of images of each class on each client.
    Cifar10_split.zip,
    Cifar100_split.zip      (if included) The generated client files we trained on. Unzip into
                            dataset/Cifar10/ and dataset/Cifar100/ of the code.

3_Paper
    Fed-GDBD_Paper.pdf      The paper (8 pages, IEEE conference format).
    Fed-GDBD_Paper_LaTeX.zip  Its LaTeX source. Compiles with pdflatex or on Overleaf.
    Full_Version/           Longer 13-page version (with appendices) and its LaTeX source.

4_Additional
    Course report (PDF for print, soft-copy PDF and Word), presentation slides,
    and the plagiarism / AI-check reports (Check_Reports/).
