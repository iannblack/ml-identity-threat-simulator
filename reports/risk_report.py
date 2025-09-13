import argparse, json
from jinja2 import Template
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--findings', required=True); ap.add_argument('--out', required=True)
    args=ap.parse_args()
    with open(args.findings) as f: data=json.load(f)
    with open('reports/templates/report.md.j2') as f: tmpl=Template(f.read())
    md=tmpl.render(findings=data.get('findings',[]))
    with open(args.out,'w') as f: f.write(md)
    print(f'Wrote {args.out}')
