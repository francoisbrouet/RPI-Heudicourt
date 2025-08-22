#!/usr/bin/gnuplot

reset
set encoding utf8

#set terminal wxt
set terminal png font "Sans,12"
set output "./temptail.png"

#set key at screen 0.13,0.80 samplen 1.0 spacing 1.2
set key opaque box linewidth 0.5
#set key bottom left horizontal maxcols 1 width 0
set key bottom left
set key font ",8"
set tics scale 0.5

set style line 1 lc 1 lw 1 lt 1
set style line 2 lc 3 lw 1 lt 1
set style line 3 lc 2 lw 1 lt 1
set style line 4 lc 4 lw 1 lt 1
set style line 5 lc 5 lw 1 lt 1
set style line 6 lc 6 lw 1 lt 1

set title ""
set grid

set xdata time
set timefmt "%y/%m/%d %H:%M:%S"
set format x "%d/%m\n%H:%M"
set xtics "24/1/1",43200,"25/1/1"

set yrange [-10:23]
set ylabel "Température [°C]"

#set mytics 5
#set ytics -20.0,10.0,50.0

plot "./temptail.dat" u 1:3 w l ls 1 title "salon", \
     "" u 1:4 w l ls 2 title "cour", \
     "" u 1:5 w l ls 3 title "cellier", \
     "" u 1:6 w l ls 4 title "grenier", \
     "" u 1:7 w l ls 5 title "chaufferie", \
     "" u 1:8 w l ls 6 title "fioul"
