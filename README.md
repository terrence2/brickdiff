# brickdiff
Command line LEGO set and part management and optimization.

## Usage Examples

### Example 1: How to build a new set or moc from existing parts (without breaking the bank).

The project: it's been over two years since the Mobile Crane Mk II (42009-1) got built and deployed to liven up my office: 
it's time to redecorate. I had no money when Mobile Crane \[Mk 1\] (8053-1), was released, and I've always
wanted to build it. Let's see if we can use the bigger set to build the smaller one on the cheap.

First, create a new repo for the project.
```bash
$ mkdir mobile-crane-mk1 && cd mobile-crane-mk1
$ brickdiff init <bricklink credentials file>
```

The bricklink credentials file must be a json format file of the form:
```javascript
{
  "consumer": {
    "key": "______",
    "secret": "_______"
  },
  "access": {
    "key": "______",
    "secret": "_______"
  }
}
```

Before we start, let's see if we can just buy the thing and skip this whole example.
```bash
$ brickdiff info --Set 8053-1: Mobile Crane
  Set 8053-1: Mobile Crane
    Brick Count:   1344
    Dimensions:    (57.8s, 37.6s, 8.4s) @ 2045.0g
    Year Released: 2010
    Category ID:   36
    New:           $170.0000 - $240.3145 - $339.7442 | 36 in 31 stores
    Used:          $90.9015 - $124.8575 - $170.4402 | 24 in 17 storesset 8053-1
```

Noooope! It's not like this set is on my bucket list or anything, so we're going to need to go cheaper. To make things interesting, I'm putting
a hard ceiling of $12. on my outlay: gotta save up for 42005-1 after all.

To get started, let's add the Mobile Crane Mk II to the repo.
```bash
$ brickdiff add --set 42009-1
```

Now we can diff to find out what parts are missing.
```bash
$ brickdiff diff --set 8053-1
  ... distressingly long (and expensive) list of differences ...
  Missing 78 different kinds of parts, 447 total bricks.
  Likely cost to buy new parts: Min $73.86 | Avg $181.01 | Max $1196.58
```

Well, we don't really need new parts anyway, do we? Let's try again looking for used parts.
  
```bash
$ brickdiff diff --set 8053-1 --used
  ... still distressingly long (but less expensive) list of differences ...
  Missing 78 different kinds of parts, 447 total bricks:
  Likely cost to buy used parts: Min $38.99 | Avg $102.33 | Max $936.78
```

That's better, but still at least 4-8x more than we've allocated for this project. For 447 bricks,
we'd expect our average cost to be something like $22.35. We need to find out why it's 5x more than
it should be. Let's look closer at the actual bricks our diff printed out:

```bash
    1 -    48452cx1:085 - $  3.12 - Technic Turntable Large Type 2, Complete Assembly
    8 -       32278:086 - $  3.74 - Technic, Liftarm 1 x 15 Thick
    8 -        3703:003 - $  6.88 - Technic, Brick 1 x 16 with Holes
    1 -       64393:003 - $  9.13 - Technic, Panel Fairing # 6 Long Smooth, Side B
    1 -       64681:003 - $  9.28 - Technic, Panel Fairing # 5 Long Smooth, Side A
    8 -    56145c02:011 - $  9.44 - Wheel 30.4mm D. x 20mm with No Pin Holes and Reinf
    8 -       55976:011 - $  9.65 - Tire 56 x 26 Balloon
```

This begs some immediate questions:
1. Why do we need a $3 turntable? The MkII has one so why isn't it being used?
2. Why are Panel Fairings almost $10 each? That's insane.
3. I know tires are expensive, but $2 each?

Let's look at that turntable first, because we know that has to be wrong.
```bash
$ brickdiff diff --set 8053-1 | grep -i "turntable large"
    1 -    48452cx1:085 - $  3.12 - Technic Turntable Large Type 2, Complete Assembly
$ brickdiff list --bricks | grep -i "turntable large"
    1 -    48452cx1:086: Technic Turntable Large Type 2, Complete Assembly with Black Outside G
```

Ah, color 85 vs 86: gray vs black outsides. You can't even see the color where it's buried, so we should be fine
using the turntable from the MkII.

We could probably just make a note to ourselves not to buy this part and be fine,
but we're not done with the changes yet and the part buying process is already fraught enough without having to tack on
exceptions. Instead of remembering this ourselves, let's make the change in a way that we can preserve it.

We'll do this by first parting it out to a csv "bill of materials" file, 
```bash
$ brickdiff partout --set 8053-1
  Wrote 145 rows to 8053-1.partout.bd.csv
```

And copy it to a new file we can customizing without losing the original.
```bash
$ cp 8053-1.partout.bd.csv custom.8053-1.bd.csv
```

Let's check that the export worked and that everything is still working properly.
```bash
$ brickdiff diff --bom custom.8053-1.bd.csv --used
  ... output ...
```
Hopefully, this gives the same results as looking at the set directly.

Now let's swap the color on 48452cx1 from 85 to 86 so that the diff will automatically use our compatible part.
To do this we can edit the file directly in our favorite editor, or use sed to edit it in place.
```bash
$ sed -i 's/48452cx1,85/48452cx1,86/' custom.8053-1.bd.csv
```

And when we diff again:
```bash
$ brickdiff diff --bom custom.8053-1.bd.csv --used
  ... a bunch of bricks, but no turntable ...
  Missing 77 different kinds of parts, 446 total bricks:
  Likely cost to buy used parts: Min $37.24 | Avg $99.21 | Max $916.83
```
We see that the price of our parts has gone down accordingly. Yay!


Next let's look at those marvelously expensive panel fairings. We can knock 20% off the price if we can figure out
a way make those cheaper.

```bash
$ brickdiff info --brick 64393:3 64681:3
  Brick 64393:3
    Part 64393 - Technic, Panel Fairing # 6 Long Smooth, Side B
      Year Released: 2009
      Dimensions:    (11.0s, 3.0s, 2.0s) @ 4.0g
      Is Obsolete:   False
      Category ID:   154
    Color 3: Yellow
      Code: f7d117
      Type: Solid
    Prices:
      New:  $7.0000 - $12.5011 - $41.8995 | 479 in 54 stores
      Used: $6.9312 - $9.1350 - $14.2034 | 65 in 21 stores
  Brick 64681:3
    Part 64681 - Technic, Panel Fairing # 5 Long Smooth, Side A
      Year Released: 2009
      Dimensions:    (11.0s, 3.0s, 2.0s) @ 4.0g
      Is Obsolete:   False
      Category ID:   154
    Color 3: Yellow
      Code: f7d117
      Type: Solid
    Prices:
      New:  $7.4050 - $12.4845 - $41.8995 | 478 in 55 stores
      Used: $7.4994 - $9.2769 - $14.2829 | 73 in 25 stores
```

Well, that's not too surprising. Released in 2009 though? The same year as the kit we're building? Suspicious.

```bash
$ brickdiff supersets --brick 64393:3 64681:3
  8109-1   Flatbed Truck
  8053-1   Mobile Crane
  8043-1   Motorized Excavator
```

Ah, they are only in three kits and are thus classified (and priced as) "rare". Let's see what our options are:
```bash
$ brickdiff info --part 64393
  Part 64393 - Technic, Panel Fairing # 6 Long Smooth, Side B
    Year Released: 2009
    Dimensions:    (11.0s, 3.0s, 2.0s) @ 4.0g
    Is Obsolete:   False
    Category ID:   154
    Colors:
      1 - White
      2 - Tan
      3 - Yellow
      5 - Red
      11 - Black
      36 - Bright Green
      42 - Medium Blue
      63 - Dark Blue
      86 - Light Bluish Gray
```
Tan is the closest color-wise, but it would look ridiculous with the yellow. On the other hand, there's
enough black in the set that we could probably change a couple of other beams and have a very nice looking
build. Let's see if the equivalent black fairings are any cheaper.

```bash
$ brickdiff info --brick 64393:11
  Brick 64393:11
    Part 64393 - Technic, Panel Fairing # 6 Long Smooth, Side B
      Year Released: 2009
      Dimensions:    (11.0s, 3.0s, 2.0s) @ 4.0g
      Is Obsolete:   False
      Category ID:   154
    Color 11: Black
      Code: 212121
      Type: Solid
    Prices:
      New:  $1.2536 - $2.0224 - $5.0000 | 878 in 101 stores
      Used: $1.2378 - $1.4466 - $1.7046 | 13 in 12 stores
```
Almost 10x cheaper! Let's update the csv and try diffing again.

```bash
$ sed -i 's/64393,3/64393,11/' custom.8053-1.bd.csv 
$ sed -i 's/64681,3/64681,11/' custom.8053-1.bd.csv 
$ brickdiff diff --bom custom.8053-1.bd.csv  --used
  ... bricks ...
  Missing 77 different kinds of parts, 446 total bricks:
  Likely cost to buy used parts: Min $25.01 | Avg $83.68 | Max $892.89
```
Now we're getting somewhere!

In order for that not to look terrible, we'll need to also make the top and sides of the cockpit
black. I think the 3 and 5 long lift bars at the top and the double-bent bars at the sides should
be good enough.
6145c02,11,8,Black - Wheel 30.4mm D. x 20mm with No Pin Holes and Reinforced Rim with Black Tire 56 x 26 Balloon (56145 / 55976)
terrence@INDRII ~/Projects/brickdiff
```diff
$ diff -uiw 8053-1.partout.bd.csv custom.8053-1.bd.csv
--- 8053-1.partout.bd.csv       Tue Jun  7 20:48:12 2016
+++ custom.8053-1.bd.csv        Tue Jun  7 23:53:36 2016
@@ -22,7 +22,7 @@
 61927c01,86,1,Light Bluish Gray - Technic Linear Actuator with Dark Bluish Gray Ends
 6553,86,4,Light Bluish Gray - Technic Pole Reverser Handle
 32012,85,1,Dark Bluish Gray - Technic Reel 3 x 2
-48452cx1,85,1,"Dark Bluish Gray - Technic Turntable Large Type 2, Complete Assembly with Black Outside Gear Section"
+48452cx1,86,1,"Dark Bluish Gray - Technic Turntable Large Type 2, Complete Assembly with Black Outside Gear Section"
 3737,11,2,"Black - Technic, Axle 10"
 3708,11,6,"Black - Technic, Axle 12"
 32062,5,34,"Red - Technic, Axle 2 Notched"
@@ -75,7 +75,8 @@
 32525,3,2,"Yellow - Technic, Liftarm 1 x 11 Thick"
 32525,86,12,"Light Bluish Gray - Technic, Liftarm 1 x 11 Thick"
 32525,85,1,"Dark Bluish Gray - Technic, Liftarm 1 x 11 Thick"
-32009,3,8,"Yellow - Technic, Liftarm 1 x 11.5 Double Bent Thick"
+32009,3,6,"Yellow - Technic, Liftarm 1 x 11.5 Double Bent Thick"
+32009,11,2,"Black - Technic, Liftarm 1 x 11.5 Double Bent Thick"
 41239,85,10,"Dark Bluish Gray - Technic, Liftarm 1 x 13 Thick"
 41239,3,8,"Yellow - Technic, Liftarm 1 x 13 Thick"
 32278,11,4,"Black - Technic, Liftarm 1 x 15 Thick"
@@ -85,8 +86,8 @@
 60483,86,10,"Light Bluish Gray - Technic, Liftarm 1 x 2 Thick with Pin Hole and Axle Hole"
 41677,5,8,"Red - Technic, Liftarm 1 x 2 Thin"
 41677,86,8,"Light Bluish Gray - Technic, Liftarm 1 x 2 Thin"
-32523,3,6,"Yellow - Technic, Liftarm 1 x 3 Thick"
-32523,11,13,"Black - Technic, Liftarm 1 x 3 Thick"
+32523,3,4,"Yellow - Technic, Liftarm 1 x 3 Thick"
+32523,11,15,"Black - Technic, Liftarm 1 x 3 Thick"
 6632,7,2,"Blue - Technic, Liftarm 1 x 3 Thin"
 6632,5,2,"Red - Technic, Liftarm 1 x 3 Thin"
 6632,85,7,"Dark Bluish Gray - Technic, Liftarm 1 x 3 Thin"
@@ -94,7 +95,8 @@
 32449,3,16,"Yellow - Technic, Liftarm 1 x 4 Thin"
 32449,11,12,"Black - Technic, Liftarm 1 x 4 Thin"
 2825,11,2,"Black - Technic, Liftarm 1 x 4 Thin with Stud Connector"
-32316,3,21,"Yellow - Technic, Liftarm 1 x 5 Thick"
+32316,3,19,"Yellow - Technic, Liftarm 1 x 5 Thick"
+32316,11,2,"Black - Technic, Liftarm 1 x 5 Thick"
 32017,3,2,"Yellow - Technic, Liftarm 1 x 5 Thin"
 32524,3,9,"Yellow - Technic, Liftarm 1 x 7 Thick"
 32524,86,4,"Light Bluish Gray - Technic, Liftarm 1 x 7 Thick"
@@ -118,8 +120,8 @@
 62531,3,2,"Yellow - Technic, Panel Curved 11 x 3 with 2 Pin Holes through Panel Surface"
 87080,3,2,"Yellow - Technic, Panel Fairing # 1 Small Smooth Short, Side A"
 87086,3,2,"Yellow - Technic, Panel Fairing # 2 Small Smooth Short, Side B"
-64681,3,1,"Yellow - Technic, Panel Fairing # 5 Long Smooth, Side A"
-64393,3,1,"Yellow - Technic, Panel Fairing # 6 Long Smooth, Side B"
+64681,11,1,"Yellow - Technic, Panel Fairing # 5 Long Smooth, Side A"
+64393,11,1,"Yellow - Technic, Panel Fairing # 6 Long Smooth, Side B"
 4274,86,15,"Light Bluish Gray - Technic, Pin 1/2"
 32002,85,3,"Dark Bluish Gray - Technic, Pin 3/4"
 6558,7,76,"Blue - Technic, Pin 3L with Friction Ridges Lengthwise"
```

