# Speculative Redesign Idea

Ok. I may do a radical redesign of the whole concept. Because we are splitting Hues and Lighting/Chromas we can proceed with a much smaller search space.

The only input is a Hue (not a color)
(Round to the nearest 5 degrees)
The Harmony is chosen and generates other cousin hues (not colors)
Foreach Hue:
	Find the maximal chroma in-srgb gamut OKLCLH H, C, L. called the "cusp" in some sources
	Generate siblings. All siblings will have reduced chroma from the base, and increased or decreased lightness:
	Find 1, 2, or 3 points -0.08 C to the left
	Find 3, 4, or 5 poitns -0.16 C to the left
	Find 5, 6, or 7 points -0.24 C to the left (if not graysnapped)
		Note: Tune all these numbers and needs a more thought little thought
	Generate "OffBlack" And "OffWhite" for this hue as well (if not already covered)
This is the Full Extended Palette for the hues

From Here, the Mapping of the palette will label these extended palette members use logic like
	Hue X Max (cusp point)
	Hue X Light
	Hue X Dark
	Hue X Light Desat
	Hue X Dark Desat
	Hue X OffWhite
	Hue X OffBlack

Bright = Max and Light
Neutral = OffWhite, offBlack , Offgray or achromatic

(Note for exploration - this seems like I am just building my own fixed member color catalogue. Can't I just use an off the shelf version?)

And then use the labeling with different rulesets:
Not all mappings can be used for a given flow as Mapping requires Harmony members to be defined.

Subdued Mapping A
	The HighLight is always the input hue, Bright (High Chroma + Light) Color
	The main costume will always be a neutral or offwhite offblack of a analogous Hue
	The secondary costume will be a analogous color with medium
Subdued Mapping B
	The HighLight is always the input hue, Bright (High Chroma + Light) Color
	The main costume will always be a neutral or offwhite offblack of a Complementary Hue
	The secondary costume will be a achromatic color
Clown Mapping A
	The main costume will be a bright color of input
	The secondary costume will be a bright complement
(etc)
