"""Local retrieval-grounded farming knowledge assistant (no external LLM/API)."""
import json, os, re, math
from collections import Counter
_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge.json")
UNKNOWN = ("I could not find a sufficiently relevant entry in our current knowledge library. "
           "I would rather not invent a traditional practice. Please ask a knowledgeable local farmer, "
           "community elder or agricultural extension worker, and add a consented, sourced note to the library.")
STOP = {"how","what","can","does","the","for","and","with","from","make","use","using","need","help","my","our","your","plant","plants","crop","crops","farm","field","tell","about","please","which","when","why","into","that","this","are","you","is","a","an","to","of","in","on","i","we","should","do","get","good","best","advice","tell","me"}
def _entries():
    with open(_P, encoding="utf-8") as f: return json.load(f)
def _tokens(s): return [x for x in re.findall(r"[a-z\u0900-\u097f]+", str(s).lower()) if x not in STOP and len(x)>1]
def _stem(t):
    if t.endswith("ly") and len(t)>5: return t[:-2]
    if t.endswith("ies") and len(t)>5: return t[:-3]+"y"
    if t.endswith("s") and len(t)>4: return t[:-1]
    return t
def retrieve(question, entries=None, limit=3):
    qt=list(dict.fromkeys(_stem(t) for t in _tokens(question)))
    if not qt: return []
    docs=[]
    for e in (entries if entries is not None else _entries()):
        title=set(_stem(t) for t in _tokens(e.get("title","")))
        kws=set(_stem(t) for t in _tokens(" ".join(e.get("keywords",[]))))
        body=set(_stem(t) for t in _tokens(e.get("text","")))
        matched=[]; total=0
        generic={"natural","organic","chemical","practice","traditional","farm","soil"}
        for t in qt:
            weight=(0.35 if t in generic else 4.0) if t in kws else (0.35 if t in generic else 3.0) if t in title else (0.2 if t in generic else 1.0) if t in body else 0.0
            total += weight
            if weight: matched.append((t,weight))
        score=sum(w for _,w in matched)/max(4.0,4.0*len(qt))
        if not matched: continue
        qnorm=" ".join(qt); title_norm=" ".join(_stem(t) for t in _tokens(e.get("title","")))
        if title_norm and title_norm in qnorm: score += .15
        docs.append((min(1.0,score),e))
    docs.sort(key=lambda x:x[0],reverse=True)
    return [{"id":e.get("id",""),"title":e.get("title","Traditional practice"),"text":e.get("text",""),"source":e.get("source","Source not recorded"),"verified_by":e.get("verified_by","Not independently verified"),"score":round(sc,3),"language":e.get("language","en")} for sc,e in docs[:limit] if sc>=.12]
def search(question, entries=None):
    hits=retrieve(question,entries)
    if not hits: return {"answer":UNKNOWN,"title":"No reliable match found","matched":False,"sources":[]}
    # Retrieval-grounded response: quote the relevant records rather than inventing new recipes.
    lead="Namaste. Here is a practice from the knowledge we have collected. Please adapt it to your local soil, crop and season: "
    answer=lead+hits[0]["text"]
    answer += "\n\nA note of care: these are community knowledge records, not a diagnosis. Try a small area first and seek local agronomy advice for severe pest, disease or soil problems."
    relevant=[h for h in hits if h["score"] >= hits[0]["score"]*.65][:2]
    return {"answer":answer,"title":hits[0]["title"],"matched":True,"sources":[{"id":h["id"],"title":h["title"],"source":h["source"],"verified_by":h["verified_by"],"score":h["score"]} for h in relevant]}
