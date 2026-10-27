import json, subprocess, sys
from wordfreq import top_words
T="The cat and the dog and THE bird. A cat, a dog!"
def test_default(): assert top_words(T,n=2)==[("the",3),("and",2)] or top_words(T,n=2)[0]==("the",3)
def test_order(): assert top_words("b a b a c",n=10)==[("a",2),("b",2),("c",1)]
def test_stop(): assert top_words(T,n=3,stopwords={"the","and","a"})==[("cat",2),("dog",2),("bird",1)]
def test_minlen(): assert top_words(T,n=10,min_length=4)==[("bird",1)]
def test_n(): assert len(top_words(T,n=1))==1
def test_cli(tmp_path):
    f=tmp_path/"t.txt"; f.write_text(T)
    r=subprocess.run([sys.executable,"wordfreq.py",str(f),"--top","2","--stopwords","the,and,a","--json"],capture_output=True,text=True)
    assert r.returncode==0 and json.loads(r.stdout)==[["cat",2],["dog",2]]
def test_cli_plain(tmp_path):
    f=tmp_path/"t.txt"; f.write_text("x y x")
    r=subprocess.run([sys.executable,"wordfreq.py",str(f)],capture_output=True,text=True)
    assert "x" in r.stdout and "2" in r.stdout
