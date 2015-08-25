/* Copyright 2006 DJ Delorie, distributed under the terms of the GPL v2 */

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define LINESIZE (int)(1000.0/72.0)
#define LINESIZEPT 1

/* Copyright (C) 1995 DJ Delorie, see COPYING.DJ for details */

float fm_hlv[] = {
  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
  ,0.277979 ,0.277979 ,0.35498 ,0.555981 ,0.555981 ,0.888989 ,0.666992
  ,0.221997 ,0.332983 ,0.332983 ,0.388989 ,0.583984 ,0.277979
  ,0.332983 ,0.277979 ,0.277979 ,0.555981 ,0.555981 ,0.555981
  ,0.555981 ,0.555981 ,0.555981 ,0.555981 ,0.555981 ,0.555981
  ,0.555981 ,0.277979 ,0.277979 ,0.583984 ,0.583984 ,0.583984
  ,0.555981 ,1.01499 ,0.666992 ,0.666992 ,0.721997 ,0.721997 ,0.666992
  ,0.610986 ,0.777979 ,0.721997 ,0.277979 ,0.5 ,0.666992 ,0.555981
  ,0.832983 ,0.721997 ,0.777979 ,0.666992 ,0.777979 ,0.721997
  ,0.666992 ,0.610986 ,0.721997 ,0.666992 ,0.943994 ,0.666992
  ,0.666992 ,0.610986 ,0.277979 ,0.277979 ,0.277979 ,0.468994
  ,0.555981 ,0.221997 ,0.555981 ,0.555981 ,0.5 ,0.555981 ,0.555981
  ,0.277979 ,0.555981 ,0.555981 ,0.221997 ,0.221997 ,0.5 ,0.221997
  ,0.832983 ,0.555981 ,0.555981 ,0.555981 ,0.555981 ,0.332983 ,0.5
  ,0.277979 ,0.555981 ,0.5 ,0.721997 ,0.5 ,0.5 ,0.5 ,0.333984
  ,0.259985 ,0.333984 ,0.583984 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0
  ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0
  ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0
  ,0.0 ,0.332983 ,0.555981 ,0.555981 ,0.166992 ,0.555981 ,0.555981
  ,0.555981 ,0.555981 ,0.190991 ,0.332983 ,0.555981 ,0.332983
  ,0.332983 ,0.5 ,0.5 ,0.0 ,0.555981 ,0.555981 ,0.555981 ,0.277979
  ,0.0 ,0.536987 ,0.35 ,0.221997 ,0.332983 ,0.332983 ,0.555981 ,1.0
  ,1.0 ,0.0 ,0.610986 ,0.0 ,0.332983 ,0.332983 ,0.332983 ,0.332983
  ,0.332983 ,0.332983 ,0.332983 ,0.332983 ,0.0 ,0.332983 ,0.332983
  ,0.0 ,0.332983 ,0.332983 ,0.332983 ,1.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0
  ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,1.0 ,0.0
  ,0.369995 ,0.0 ,0.0 ,0.0 ,0.0 ,0.555981 ,0.777979 ,1.0 ,0.36499 ,0.0
  ,0.0 ,0.0 ,0.0 ,0.0 ,0.888989 ,0.0 ,0.0 ,0.0 ,0.277979 ,0.0 ,0.0
  ,0.221997 ,0.610986 ,0.943994 ,0.610986 ,0.0 ,0.0 ,0.0 ,0.0 };


char **sym;
int nsym;

typedef struct {
  int type;
  int size;
  int color;
  int index;
} Sortable;

Sortable *sort;
int nsort = 0;

void
save_sort (int type, int size, int color, int index)
{
  sort[nsort].type = type;
  sort[nsort].color = color;
  sort[nsort].size = size;
  sort[nsort].index = index;
  nsort ++;
}

void *
xrealloc (void *v, int n)
{
  if (v)
    return realloc (v, n);
  return malloc (n);
}

char *
safe_fgets (FILE *f)
{
  static char *buffer = 0;
  static int bufsize = 0;
  int bufptr;
  int ch;

  bufptr = 0;

  while (1)
    {
      ch = fgetc(f);
      if (ch == EOF)
	{
	  if (bufptr == 0)
	    return 0;
	  buffer[bufptr] = 0;
	  return buffer;
	}
      if (ch == '\r')
	continue;
      if (bufsize <= bufptr)
	{
	  bufsize += 10;
	  buffer = (char *) xrealloc (buffer, bufsize+1);
	  if (buffer == 0)
	    {
	      fprintf(stderr, "Out of memory! bufsize %d\n", bufsize);
	      exit(1);
	    }
	}
      buffer[bufptr++] = ch;
      if (ch == '\n')
	{
	  buffer[bufptr-1] = 0;
	  return buffer;
	}
    }
}

void
read_symfile (FILE *f)
{
  char *line;
  int msym = 0;
  while (line = safe_fgets(f))
    {
      if (msym <= nsym)
	{
	  msym += 10;
	  sym = (char **) xrealloc (sym, msym*sizeof(char *));
	}
      while (*line && isspace(*line))
	line++;
      sym[nsym++] = strdup(line);
    }
}

int minx=1<<30, maxx=-(1<<30), miny=1<<30, maxy=-(1<<30);

void
coord(int x, int y, int w)
{
  w /= 2;
  if (minx > x - w) minx = x - w;
  if (maxx < x + w) maxx = x + w;
  if (miny > y - w) miny = y - w;
  if (maxy < y + w) maxy = y + w;
}

int
ps_length(char *t, int size)
{
  float l = 0;
  while (*t)
    {
      l += fm_hlv[(*t) & 0xff] * size;
      t++;
    }
  return (int)l;
}

void
scan_extents ()
{
  int i, j;
  int x, y, w, h, x1, y1, x2, y2, n, s, r, v, avc, a, align;
  int c;

  for (i=0; i<nsym; i++)
    {
      char *line = sym[i];
      switch (line[0])
	{
	case 'L': /* pin */
	  sscanf(line, "%*c %d %d %d %d %d %d", &x1, &y1, &x2, &y2, &c, &s);
	  save_sort('L', c, s, i);
	  coord(x1, y1, s);
	  coord(x2, y2, s);
	  break;

	case 'H': /* path */
	  {
	    int color, width, capstyle, dashstyle, dashlength, dashspace;
	    int filltype, fillwidth, angle1, pitch1, angle2, pitch2, num_lines;

	    /*                co wi lc ds dl sp fi wf fa fp sa sp N */
	    sscanf(line, "%*c %d %d %d %d %d %d %d %d %d %d %d %d %d",
		   &color, &width, &capstyle, &dashstyle, &dashlength, &dashspace,
		   &filltype, &fillwidth, &angle1, &pitch1, &angle2, &pitch2, &num_lines);
	    save_sort('H', color, width, i);
	    for (j=0; j<num_lines; j++)
	      {
		char lcode;
        sscanf (sym[i+j+1], "%c %d*c%d", &lcode, &x1, &y1);
		switch (lcode)
		  {
		  case 'M':
		  case 'L':
		    x = x1;
		    y = y1;
		    coord (x, y, width);
		    break;
		  case 'm':
		  case 'l':
		    x += x1;
		    y += y1;
		    coord (x, y, width);
		    break;
		  case 'Z':
		  case 'z':
		    break;
		  case 'H':
		    x = x1;
		    coord (x, y, width);
		    break;
		  case 'h':
		    x += x1;
		    coord (x, y, width);
		    break;
		  case 'V':
		    y = x1;
		    coord (x, y, width);
		    break;
		  case 'v':
		    y += x1;
		    coord (x, y, width);
		    break;
		  }
	      }
	    i += num_lines;
	    break;
	  }

	case 'G': /* picture */
	  i ++;
	  break;

	case 'B': /* box */
	  sscanf(line, "%*c %d %d %d %d %d %d", &x, &y, &w, &h, &c, &s);
	  save_sort('B', c, s, i);
	  coord(x, y, s);
	  coord(x+w, y+h, s);
	  break;

	case 'V': /* circle */
	  sscanf(line, "%*c %d %d %d %d %d", &x, &y, &r, &c, &s);
	  save_sort('V', c, s, i);
	  coord (x-r, y-r, s);
	  coord (x+r, y+r, s);
	  break;

	case 'A': /* arc */
	  sscanf(line, "%*c %d %d %d %*d %*d %d %d", &x, &y, &r, &c, &s);
	  save_sort('A', c, s, i);
	  coord (x-r, y-r, s);
	  coord (x+r, y+r, s);
	  break;

	case 'T':
	  sscanf(line, "%*c %d %d %d %d %d %d %d %d %d", &x, &y, &c, &s, &v, &avc, &a, &align, &n);
	  save_sort('T', c, s, i);
	  s = (int)(s * 1000.0 / 72.0 * 1.3);
	  if (v)
	    {
	      int xo, yo;
	      for (j=0; j<n; j++)
		{
		  int len;
		  char *text = sym[j+i];
		  switch (avc) {
		  case 1:
		    if (strchr(text, '='))
		      text = strchr(text, '=') + 1;
		    break;
		  case 2:
		    if (strchr(text, '='))
		      *(strchr(text, '=')) = 0;
		    break;
		  }
		  len = ps_length(text, s);

		  switch (align / 3) {
		  case 0: xo = 0; break;
		  case 1: xo = len/2; break;
		  case 2: xo = len; break;
		  }
		  switch (align % 3) {
		  case 0: yo = 0; break;
		  case 1: yo = (int)(s * 0.35); break;
		  case 2: yo = (int)(s * 0.7); break;
		  }

		  switch (a) {
		  case 0:
		    coord(x-xo, y-yo, 0);
		    coord(x-xo+len, y-yo+s, 0);
		    break;
		  case 90:
		    coord(x+yo, y-xo, 0);
		    coord(x+yo-s, y-xo+len, 0);
		    break;
		  case 180:
		    coord(x+xo, y+yo, 0);
		    coord(x+xo-len, y+yo-s, 0);
		    break;
		  case 270:
		    coord(x-yo, y+xo, 0);
		    coord(x-yo+s, y+xo-len, 0);
		    break;
		  }
		}
	    }
	  i += n;
	  break;

	case 'N': /* net */
	case 'U': /* bus */
	case 'P': /* pin */
	  sscanf(line, "%*c %d %d %d %d %d", &x1, &y1, &x2, &y2, &c);
	  save_sort(line[0], c, LINESIZE, i);
	  coord(x1, y1, LINESIZE);
	  coord(x2, y2, LINESIZE);
	  break;
	}
    }

}

#define MARGIN 20

int
sort_func (const void *va, const void *vb)
{
  Sortable *a = (Sortable *)va;
  Sortable *b = (Sortable *)vb;
  if (a->type != b->type)
    return a->type - b->type;
  if (a->size != b->size)
    return a->size - b->size;
  if (a->color != b->color)
    return a->color - b->color;
  return a->index - b->index;
}

const char * colormap[] = {
  "1.0 1.0 1.0", /* background */
  "0.0 0.0 0.0", /* white */
  "0.8 0.0 0.0", /* red */
  "0.0 0.5 0.0", /* green */
  "0.0 0.0 1.0", /* blue */
  "0.5 0.5 0.0", /* yellow */
  "0.0 0.5 0.5", /* cyan */
  "0.0 0.5 0.5", /* ? */
  "0.8 0.0 0.0", /* red */
  "0.0 0.5 0.0", /* green */
  "0.0 0.5 0.0", /* green */
  "0.9 0.4 0.0", /* orange */
  "0.9 0.4 0.0", /* orange */
  "0.0 0.5 0.5", /* cyan */
  "0.6 0.6 0.6", /* grey90 */
  "0.4 0.4 0.4", /* grey */
  "0.6 0.0 0.6", /* "other" */
};
#define NUM_COLORS (sizeof(colormap)/sizeof(colormap[0]))

void
color_size (FILE *f, int c, int s)
{
  static int oc = -1;
  static int os = -100;
  if (oc != c)
    {
      if (c < 0 || c >= NUM_COLORS)
	c = NUM_COLORS-1;
      fprintf(f, "%s setrgbcolor\n", colormap[c]);
      oc = c;
    }
  if (os != s)
    {
      if (s < LINESIZEPT)
	s = LINESIZEPT;
      fprintf(f, "%d setlinewidth\n", s);
      os = s;
    }
}

void
write_eps (const char *filename, FILE *f)
{
  int i, j, si;
  int x, y, w, h, x1, y1, x2, y2, n, s, r, v, avc, a, align;
  int c;
  double scale = 1.0;
  if (maxx - minx > 10000
      || maxy - miny > 15000)
    scale = 0.5;

  minx -= MARGIN;
  miny -= MARGIN;
  maxx += MARGIN;
  maxy += MARGIN;

  fprintf(f, "%!PS-Adobe-3.0 EPSF-3.0\n");
  fprintf(f, "%%%%BoundingBox: 0 0 %g %g\n",
	  (maxx-minx)/1000.0 * 72 * scale, (maxy-miny)/1000.0 * 72 * scale);
  fprintf(f, "%%%%Pages: 1\n");
  fprintf(f, "save countdictstack mark newpath /showpage {} def /setpagedevice {pop} def\n");
  fprintf(f, "%%%%EndProlog\n");
  fprintf(f, "%%%%Page: 1 1\n");
  fprintf(f, "%%%%BeginDocument: %s\n", filename);
  fprintf(f, "%g dup scale\n", 72.0/1000.0 * scale);
  fprintf(f, "%d %d translate\n", -minx, -miny);

  fprintf(f, "/t { gsave translate rotate moveto show grestore } bind def\n");

  qsort (sort, nsort, sizeof(sort[0]), sort_func);

  for (si=0; si<nsort; si++)
    {
      i = sort[si].index;
      char *line = sym[i];
      switch (line[0])
	{
	case 'L': /* line */
	  sscanf(line, "%*c %d %d %d %d %d %d", &x1, &y1, &x2, &y2, &c, &s);
	  color_size(f, c, s);
	  fprintf(f, "%d %d moveto %d %d lineto stroke\n", x1, y1, x2, y2);
	  break;

	case 'H': /* path */
	  {
	    int color, width, capstyle, dashstyle, dashlength, dashspace;
	    int filltype, fillwidth, angle1, pitch1, angle2, pitch2, num_lines;

	    /*                co wi lc ds dl sp fi wf fa fp sa sp N */
	    sscanf(line, "%*c %d %d %d %d %d %d %d %d %d %d %d %d %d",
		   &color, &width, &capstyle, &dashstyle, &dashlength, &dashspace,
		   &filltype, &fillwidth, &angle1, &pitch1, &angle2, &pitch2, &num_lines);
	    for (j=0; j<num_lines; j++)
	      {
		char lcode;
		sscanf (sym[i+j+1], "%c %d%*c%d", &lcode, &x1, &y1);
		switch (lcode)
		  {
		  case 'M':
		    fprintf (f, "%d %d moveto\n", x1, y1);
		    x = x1; y = y1;
		    break;
		  case 'm':
		    fprintf (f, "%d %d rmoveto\n", x1, y1);
		    x += x1; y += y1;
		    break;
		  case 'L':
		    fprintf (f, "%d %d lineto\n", x1, y1);
		    x = x1; y = y1;
		    break;
		  case 'l':
		    fprintf (f, "%d %d rlineto\n", x1, y1);
		    x += x1; y += y1;
		    break;

		  case 'Z':
		  case 'z':
		    if (filltype)
		      fprintf (f, "closepath fill\n");
		    else
		      fprintf (f, "closepath stroke\n");
		    break;

		  case 'H':
		    fprintf (f, "%d %d lineto\n", x1, y);
		    x = x1;
		    break;
		  case 'h':
		    fprintf (f, "%d 0 rlineto\n", x1);
		    x += x1;
		    break;
		    coord (x, y, width);
		    break;
		  case 'V':
		    fprintf (f, "%d %d lineto\n", x, y1);
		    y = x1;
		    break;
		  case 'v':
		    fprintf (f, "0 %d rlineto\n", 0, y1);
		    y += x1;
		    break;
		  }
	      }
	    i += num_lines;
	  }
	  break;

	case 'G': /* picture */
	  i ++;
	  break;

	case 'B': /* box */
	  sscanf(line, "%*c %d %d %d %d %d %d", &x, &y, &w, &h, &c, &s);
	  color_size(f, c, s);
	  fprintf(f, "%d %d moveto %d 0 rlineto 0 %d rlineto %d 0 rlineto closepath stroke\n",
		  x, y, w, h, -w);
	  break;

	case 'V': /* circle */
	  sscanf(line, "%*c %d %d %d %d %d", &x, &y, &r, &c, &s);
	  color_size(f, c, s);
	  fprintf(f, "newpath %d %d %d 0 360 arc stroke\n",
		  x, y, r);
	  break;

	case 'A': /* arc */
	  {
	    int sang, dang;
	    sscanf(line, "%*c %d %d %d %d %d %d %d", &x, &y, &r, &sang, &dang, &c, &s);
	    color_size(f, c, s);
	    fprintf(f, "newpath %d %d %d %d %d arc stroke\n",
		    x, y, r, sang, sang+dang);
	  }
	  break;

	case 'T':
	  sscanf(line, "%*c %d %d %d %d %d %d %d %d %d", &x, &y, &c, &s, &v, &avc, &a, &align, &n);
	  if (v)
	    {
	      static double last_fsize = -1;
	      int xo, yo;
	      double linestep, fontsize;

	      fontsize = (int)(s*1000.0 / 72.0 * 1.4);
	      linestep = fontsize * 1.35;
	      s = (int)(linestep * n);

	      color_size(f, c, 0);
	      if (last_fsize != fontsize)
		{
		  last_fsize = fontsize;
		  fprintf(f, "/Helvetica findfont %g scalefont setfont\n", (double)fontsize);
		}

	      for (j=0; j<n; j++)
		{
		  int len;
		  char *text = sym[i+j+1];
		  switch (avc) {
		  case 1:
		    if (strchr(text, '='))
		      text = strchr(text, '=') + 1;
		    break;
		  case 2:
		    if (strchr(text, '='))
		      *(strchr(text, '=')) = 0;
		    break;
		  }
		  len = ps_length(text, (int)fontsize);
		  if (a == 180)
		    {
		      /* special case - text is never upside-down.  */
		      align = 8 - align;
		      yo += (int)(s * 0.3);
		      a = 0;
		    }
		  switch (align / 3) {
		  case 0: xo = 0; break;
		  case 1: xo = len/2; break;
		  case 2: xo = len; break;
		  }
		  switch (align % 3) {
		  case 0: yo = (int)(linestep * (n-1)); break;
		  case 1: yo = (int)(linestep * ((n-1)/2.0-0.3)); break;
		  case 2: yo = (int)(linestep * (-0.65)); break;
		  }
		  fprintf(f, "(");
		  char *cp;
		  for (cp = text; *cp; cp++)
		    {
		      if (*cp == '(' || *cp == ')' || *cp == '\\')
			fputc ('\\', f);
		      fputc (*cp, f);
		    }
		  fprintf(f, ") %d %d %d %d %d t\n", -xo, (int)(yo-linestep*j), a, x, y);
		}
	    }
	  i += n;
	  break;

	case 'N': /* net */
	case 'U': /* bus */
	case 'P': /* pin */
	  sscanf(line, "%*c %d %d %d %d %d", &x1, &y1, &x2, &y2, &c);
	  color_size(f, c, LINESIZEPT);
	  fprintf (f, "%d %d moveto %d %d lineto stroke\n", x1, y1, x2, y2);
	  break;
	}
    }

  fprintf(f, "showpage\n");
  fprintf(f, "%%%%EndDocument\n");
  fprintf(f, "%%%%Trailer\n");
  fprintf(f, "cleartomark countdictstack exch sub { end } repeat restore\n");
  fprintf(f, "%%%%EOF\n");
}

int
main(int argc, char **argv)
{
  FILE *symfile;
  FILE *epsfile;

  if (argc > 1)
    {
      symfile = fopen (argv[1], "r");
      if (!symfile)
	{
	  fprintf(stderr, "Error: can't open %s for reading.\n", argv[1]);
	  perror("The error was\n");
	  exit(1);
	}
    }
  else
    {
      symfile = stdin;
    }

  read_symfile(symfile);

  sort = (Sortable *) malloc (nsym * sizeof(Sortable));

  if (symfile != stdin)
    fclose (symfile);

  scan_extents();

  if (argc > 2)
    {
      epsfile = fopen (argv[2], "w");
      if (!symfile)
	{
	  fprintf(stderr, "Error: can't open %s for writing.\n", argv[2]);
	  perror("The error was\n");
	  exit(1);
	}
    }
  else
    epsfile = stdout;
  
  write_eps(argc > 2 ? argv[2] : "stdout.eps", epsfile);

  if (epsfile != stdout)
    fclose(epsfile);

  exit(0);
}
