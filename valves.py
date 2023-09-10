import sys
import re
import math

def cap(color):
	r,g,b = color
	r = 0 if r < 0 else r
	g = 0 if g < 0 else g
	b = 0 if b < 0 else b
	r = 255 if r > 255 else r
	g = 255 if g > 255 else g
	b = 255 if b > 255 else b
	return (r,g,b)
def generateEscape(color,back=False):
	r,g,b = cap(color)
	return "\033["+str(48 if back else 38)+";2;{0};{1};{2}m".format(r,g,b)
def color(s,front=None,back=None):
	if front == None and back == None:
		return str(s)+"\u001b[0m"
	elif front == None:
		return generateEscape(back,True)+str(s)+"\u001b[0m"
	elif back == None:
		return generateEscape(front)+str(s)+"\u001b[0m"
	else:
		return generateEscape(back,True)+generateEscape(front)+str(s)+"\u001b[0m"
def lerp(A,B,num=0.5):
	rA, gA, bA = A
	rB, gB, bB = A
	rM = rA * (1-num) + rB * (num)
	gM = gA * (1-num) + gB * (num)
	bM = bA * (1-num) + bB * (num)
	return (rM, gM, bM)

RPOS = [(0,-1),(1,0),(0,1),(-1,0)]

if len(sys.argv) < 2:
	print("Usage: python3 valves.py <file>")
	sys.exit(-1)

debugging = len(sys.argv) > 2
program = open(sys.argv[1]).read()

def get(l,x,y):
	#print("\t\t",(x,y),(x%width,y%height))
	return l[(x%width,y%height)]

width = max([len(a) for a in program.split("\n")])
gridarr, pump = [a.strip("\n") for a in program.split("—"*width)]
params = {}
for i in pump.split("\n"):
	if i == "":
		continue
	#print(i)
	s = [a.strip() for a in i.split("=")]
	#print(s)
	params[s[0]] = eval(s[1])
#print(params)

instr = ""
inchr = ""
inswch = 255
outswch = 255
outarr = [0,0,0,0,0,0,0,0]

#print(pumpdict)
gridarr = [[b for b in a]+[" "]*(width-len(a)) for a in gridarr.split("\n")]
height = len(gridarr)
pressurearr = [[0 for _ in range(width)].copy() for _ in range(height)]

grid = {}

for y in range(height):
	for x in range(width):
		grid[(x,y)] = gridarr[y][x]

pressure = {}

for y in range(height):
	for x in range(width):
		pressure[(x,y)] = pressurearr[y][x]

data = {
	"#": {"permittivity": lambda x, y, ih, iN: 0},
	"▓": {"permittivity": lambda x, y, ih, iN: 0.25},
	"▒": {"permittivity": lambda x, y, ih, iN: 0.5},
	" ": {"permittivity": lambda x, y, ih, iN: 1},
	"P": {"permittivity": lambda x, y, ih, iN: 1},
	"M": {"permittivity": lambda x, y, ih, iN: 1},
	"J": {"permittivity": lambda x, y, ih, iN: 1},
	"I": {"permittivity": lambda x, y, ih, iN: 1},
	"O": {"permittivity": lambda x, y, ih, iN: 1},
	"E": {"permittivity": lambda x, y, ih, iN: 1},

	"─": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [1,3,4] and iN in [1,3,4]) else 0},
	"│": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [0,2,4] and iN in [0,2,4]) else 0},

	"┌": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [0,3,4] and iN in [1,2,4]) else 0},
	"┐": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [0,1,4] and iN in [3,2,4]) else 0},
	"┘": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [1,2,4] and iN in [0,3,4]) else 0},
	"└": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [3,2,4] and iN in [0,1,4]) else 0},

	"┴": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [2,3,1,4] and iN in [0,1,3,4]) else 0},
	"├": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [2,3,0,4] and iN in [0,1,2,4]) else 0},
	"┬": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [3,0,1,4] and iN in [1,2,3,4]) else 0},
	"┤": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [2,0,1,4] and iN in [0,2,3,4]) else 0},

	"╵": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [2,4] and iN in [0,4]) else 0},
	"╴": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [1,4] and iN in [3,4]) else 0},
	"╶": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [3,4] and iN in [1,4]) else 0},
	"╷": {"permittivity": lambda x, y, ih, iN: 1 if (ih in [0,4] and iN in [2,4]) else 0},

	">": {"permittivity": lambda x, y, ih, iN: 1 if (get(pressure,x-1,y)-get(pressure,x+1,y) >= extradata[(x,y)][0]) and ((ih in [0,2,4] and iN in [0,2,4] and extradata[(x,y)][1]) or not extradata[(x,y)][1]) else 0},
	"v": {"permittivity": lambda x, y, ih, iN: 1 if (get(pressure,x,y-1)-get(pressure,x,y+1) >= extradata[(x,y)][0]) and ((ih in [1,3,4] and iN in [1,3,4] and extradata[(x,y)][1]) or not extradata[(x,y)][1]) else 0},
	"<": {"permittivity": lambda x, y, ih, iN: 1 if (get(pressure,x+1,y)-get(pressure,x-1,y) >= extradata[(x,y)][0]) and ((ih in [0,2,4] and iN in [0,2,4] and extradata[(x,y)][1]) or not extradata[(x,y)][1]) else 0},
	"^": {"permittivity": lambda x, y, ih, iN: 1 if (get(pressure,x,y+1)-get(pressure,x,y-1) >= extradata[(x,y)][0]) and ((ih in [1,3,4] and iN in [1,3,4] and extradata[(x,y)][1]) or not extradata[(x,y)][1]) else 0}
}

extradata = {}
count = {}

for y in range(height):
	for x in range(width):
		cell = get(grid,x,y)
		#print(x,y,c)
		try:
			c = count[cell]
		except KeyError:
			count[cell] = 0
			c = 0
		try:
			extradata[(x,y)] = params[cell+str(c)]
		except KeyError:
			pass
		count[cell] += 1
# print(pumpdict)
#print(extradata)

def getNeighbors(l,x,y):
	out = []
	change = False
	#print(x,y)
	if get(grid,x,y) == "J":
		change = extradata[(x,y)]
	for i in RPOS:
		out.append(get(l,x+i[0],y+i[1]))
	if change:
		for i in change.items():
			#print(i)
			out[i[0]] = get(l,x+i[1][0],y+i[1][1])
	#if get(grid,x,y) == "J":
		#print(out)
	return out

def step():
	global pressure
	global inswch
	global instr
	global inchr
	global outarr
	global outswch
	pressurenew = {}
	for y in range(height):
		for x in range(width):
			#print((x,y))
			pressurehere = get(pressure,x,y)
			permithere = [data[get(grid,x,y)]["permittivity"](x,y,4,a) for a in range(4)]
			#print("\t",permithere)
			pressureneigh = getNeighbors(pressure,x,y)
			#print(x,y)
			#print(getNeighbors(grid,x,y))
			permitneigh = [data[a[0]]["permittivity"](x+a[1][0],y+a[1][1],a[2],4) for a in zip(getNeighbors(grid,x,y),RPOS,range(8))]
			pressurechange = sum([(a[0]-pressurehere)*a[1]*a[2]*0.125 for a in zip(pressureneigh,permitneigh,permithere)])
			#print("\t",pressurehere,pressureneigh,permitneigh,pressurechange)
			#print("\t",sum(pressurechange))
			newpressure = min(max(pressurehere+pressurechange,-256),256)
			pressurenew[(x,y)] = newpressure
	for y in range(height):
		for x in range(width):
			if grid[(x,y)] == "P":
				pressurenew[(x,y)] = extradata[(x,y)]
			if grid[(x,y)] == "I":
				if extradata[(x,y)] == "STAT":
					pressurenew[(x,y)] = inswch
				if extradata[(x,y)] in [0,1,2,3,4,5,6,7]:
					if inchr == "":
						pressurenew[(x,y)] = 0
					else:
						pressurenew[(x,y)] = (2*int(bin(ord(inchr))[2:].zfill(8)[extradata[(x,y)]])-1)*255
			if grid[(x,y)] == "O":
				if extradata[(x,y)] == "STAT":
					pressurenew[(x,y)] = outswch
				if extradata[(x,y)] in [0,1,2,3,4,5,6,7]:
					outarr[extradata[(x,y)]] = pressurenew[(x,y)]
	for y in range(height):
		for x in range(width):
			if grid[(x,y)] == "E" and abs(pressurenew[(x,y)]) >=128:
				sys.exit()
			if grid[(x,y)] == "I" and extradata[(x,y)] == "CONF":
				if abs(pressurenew[(x,y)]) >= 128 and pressurenew[(x,y)] * inswch > 0:
					inswch = -inswch
					inchr = ""
					while instr == "":
						instr = input("> ")
					inchr = instr[0]
					instr = instr[1:]
			if grid[(x,y)] == "O" and extradata[(x,y)] == "CONF":
				if abs(pressurenew[(x,y)]) >= 128 and pressurenew[(x,y)] * outswch > 0:
					outswch = -outswch
					if all([abs(a) >= 128 for a in outarr]):
						print(chr(int("".join(["1" if a > 0 else "0" for a in outarr]),2)),end="",flush=True)
						if debugging:
							input("")
	pressure = pressurenew

def colorpressure(s,p,l,m,h,back=False):
	if p < 0:
		scale = -p/256
		if back:
			return color(s, back=lerp(m,l,scale))
		else:
			return color(s, front=lerp(m,l,scale))
	elif p > 0:
		scale = p/256
		if back:
			return color(s, back=lerp(m,h,scale))
		else:
			return color(s, front=lerp(m,h,scale))
	else:
		return s

def render():
	out = "\x1b[2J"
	RED = (255,0,0)
	BLU = (0,128,255)
	BCK = (0,0,0)
	WHT = (255,255,255)
	measurements = ""
	c = 0
	for y in range(height):
		for x in range(width):
			getpr = get(pressure,x,y)
			cell = get(grid,x,y)
			out += colorpressure(cell,getpr,BLU,BCK,RED,back=True)
			if cell == "M":
				measurements += "M"+str(c)+": "+colorpressure(str(getpr),getpr,BLU,WHT,RED)+"\n"
				c += 1
		out += "\n"
	return out+measurements
while True:
	if debugging:
		print(render())
	step()
