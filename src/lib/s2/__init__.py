import math

class S2(object):
    """ generated source for class S2 """
    #  Declare some frequently used constants
    M_PI = math.pi
    M_1_PI = 1.0 / math.pi
    M_PI_2 = math.pi / 2.0
    M_PI_4 = math.pi / 4.0
    M_SQRT2 = math.sqrt(2)
    M_E = math.e

    #  Together these flags define a cell orientation. If SWAP_MASK
    #  is true, then canonical traversal order is flipped around the
    #  diagonal (i.e. i and j are swapped with each other). If
    #  INVERT_MASK is true, then the traversal order is rotated by 180
    #  degrees (i.e. the bits of i and j are inverted, or equivalently,
    #  the axis directions are reversed).
    SWAP_MASK = 0x01
    INVERT_MASK = 0x02

    #  Mapping Hilbert traversal order to orientation adjustment mask.
    POS_TO_ORIENTATION = [SWAP_MASK, 0, 0, INVERT_MASK + SWAP_MASK]

    #
    # Returns an XOR bit mask indicating how the orientation of a child subcell
    # is related to the orientation of its parent cell. The returned value can
    # be XOR'd with the parent cell's orientation to give the orientation of
    # the child cell.
    #
    # @param position the position of the subcell in the Hilbert traversal, in
    #     the range [0,3].
    # @return a bit mask containing some combination of {@link #SWAP_MASK} and
    #     {@link #INVERT_MASK}.
    # @throws IllegalArgumentException if position is out of bounds.
    #
    @classmethod
    def posToOrientation(cls, position):
        """ generated source for method posToOrientation """
        #Preconditions.checkArgument(0 <= position and position < 4)
        return cls.POS_TO_ORIENTATION[position]

    #  Mapping from cell orientation + Hilbert traversal to IJ-index.
    POS_TO_IJ = [
      [0, 1, 3, 2], # canonical order: (0,0), (0,1), (1,1), (1,0)
      [0, 2, 3, 1], # axes swapped: (0,0), (1,0), (1,1), (0,1)
      [3, 2, 0, 1], # bits inverted: (1,1), (1,0), (0,0), (0,1)
      [3, 1, 0, 2], # swapped & inverted: (1,1), (0,1), (0,0), (1,0)
    ]

    #
    # Return the IJ-index of the subcell at the given position in the Hilbert
    # curve traversal with the given orientation. This is the inverse of
    # {@link #ijToPos}.
    #
    # @param orientation the subcell orientation, in the range [0,3].
    # @param position the position of the subcell in the Hilbert traversal, in
    #     the range [0,3].
    # @return the IJ-index where {@code 0->(0,0), 1->(0,1), 2->(1,0), 3->(1,1)}.
    # @throws IllegalArgumentException if either parameter is out of bounds.
    #
    @classmethod
    def posToIJ(cls, orientation, position):
        """ generated source for method posToIJ """
        #Preconditions.checkArgument(0 <= orientation and orientation < 4)
        #Preconditions.checkArgument(0 <= position and position < 4)
        return cls.POS_TO_IJ[orientation][position]


class S2CellId(object):
    """
    An S2CellId is a 64-bit unsigned integer that uniquely identifies a cell in
    the S2 cell decomposition. It has the following format:

        id = [face][face_pos]

    face: a 3-bit number (range 0..5) encoding the cube face.

    face_pos: a 61-bit number encoding the position of the center of this cell
    along the Hilbert curve over this face.

    Sequentially increasing cell ids follow a continuous space-filling curve over
    the entire sphere. They have the following properties:
     - The id of a cell at level k consists of a 3-bit face number followed by k
    bit pairs that recursively select one of the four children of each cell. The
    next bit is always 1, and all other bits are 0. Therefore, the level of a
    cell is determined by the position of its lowest-numbered bit that is turned
    on (for a cell at level k, this position is 2 * (MAX_LEVEL - k).)
     - The id of a parent cell is at the midpoint of the range of ids spanned by
    its children (or by its descendants at any level).

    Leaf cells are often used to represent points on the unit sphere, and this
    class provides methods for converting directly between these two
    representations. For cells that represent 2D regions rather than discrete
    points, it is better to use the S2Cell class.
    """

    #  Although only 60 bits are needed to represent the index of a leaf
    #  cell, we need an extra bit in order to represent the position of
    #  the center of the leaf cell along the Hilbert curve.
    FACE_BITS = 3
    NUM_FACES = 6
    MAX_LEVEL = 30

    #  Valid levels: 0..MAX_LEVEL
    POS_BITS = 2 * MAX_LEVEL + 1
    MAX_SIZE = 1 << MAX_LEVEL

    MAX_UNSIGNED = 0xffffffffffffffff

    #  The following lookup tables are used to convert efficiently between an
    #  (i,j) cell index and the corresponding position along the Hilbert curve.
    #  "lookup_pos" maps 4 bits of "i", 4 bits of "j", and 2 bits representing the
    #  orientation of the current cell into 8 bits representing the order in which
    #  that subcell is visited by the Hilbert curve, plus 2 bits indicating the
    #  new orientation of the Hilbert curve within that subcell. (Cell
    #  orientations are represented as combination of kSwapMask and kInvertMask.)
    #
    #  "lookup_ij" is an inverted table used for mapping in the opposite
    #  direction.
    #
    #  We also experimented with looking up 16 bits at a time (14 bits of position
    #  plus 2 of orientation) but found that smaller lookup tables gave better
    #  performance. (2KB fits easily in the primary cache.)
    #  Values for these constants are *declared* in the *.h file. Even though
    #  the declaration specifies a value for the constant, that declaration
    #  is not a *definition* of storage for the value. Because the values are
    #  supplied in the declaration, we don't need the values here. Failing to
    #  define storage causes link errors for any code that tries to take the
    #  address of one of these values.
    LOOKUP_BITS = 4
    SWAP_MASK = 0x01
    INVERT_MASK = 0x02
    LOOKUP_POS = [None]*(1 << (2 * LOOKUP_BITS + 2))
    LOOKUP_IJ = [None]*(1 << (2 * LOOKUP_BITS + 2))

    #
    # This is the offset required to wrap around from the beginning of the
    # Hilbert curve to the end or vice versa; see next_wrap() and prev_wrap().
    #
    WRAP_OFFSET = long(NUM_FACES) << POS_BITS

    def __init__(self, id = 0):
        """ generated source for method __init__ """
        super(S2CellId, self).__init__()
        self.id = id

    @classmethod
    def none(cls):
        """The default constructor returns an invalid cell id."""
        return cls()

    @classmethod
    def sentinel(cls):
        """
        Returns an invalid cell id guaranteed to be larger than any valid cell id.
        Useful for creating indexes.
        """
        return cls(cls.MAX_UNSIGNED)

    @classmethod
    def fromFacePosLevel(cls, face, pos, level):
        """
        Return a cell given its face (range 0..5), 61-bit Hilbert curve position
        within that face, and level (range 0..MAX_LEVEL). The given position will
        be modified to correspond to the Hilbert curve position at the center of
        the returned cell. This is a static function rather than a constructor in
        order to give names to the arguments.
        """
        return cls((long(face) << cls.POS_BITS) + (pos | 1)).parent(level)

    @classmethod
    def fromPoint(cls, p):
        """
        Return the leaf cell containing the given point (a direction vector, not
        necessarily unit length).
        """
        face = S2Projections.xyzToFace(p)
        uv = S2Projections.validFaceXyzToUv(face, p)
        i = cls.stToIJ(S2Projections.uvToST(uv[0]))
        j = cls.stToIJ(S2Projections.uvToST(uv[1]))
        return cls.fromFaceIJ(face, i, j)

    @classmethod
    def fromLatLng(cls, ll):
        """Return the leaf cell containing the given S2LatLng."""
        return cls.fromPoint(ll.toPoint())

    def toPoint(self):
        """
        Return the unit-length direction vector corresponding to the center of
        the given cell.
        """
        return S2Point.normalize(self.toPointRaw())

    def toPointRaw(self):
        """
        Return the direction vector corresponding to the center of the given cell.
        The vector returned by toPointRaw is not necessarily unit length.
        """
        #  First we compute the discrete (i,j) coordinates of a leaf cell contained
        #  within the given cell. Given that cells are represented by the Hilbert
        #  curve position corresponding at their center, it turns out that the cell
        #  returned by ToFaceIJOrientation is always one of two leaf cells closest
        #  to the center of the cell (unless the given cell is a leaf cell itself,
        #  in which case there is only one possibility).
        #
        #  Given a cell of size s >= 2 (i.e. not a leaf cell), and letting (imin,
        #  jmin) be the coordinates of its lower left-hand corner, the leaf cell
        #  returned by ToFaceIJOrientation() is either (imin + s/2, jmin + s/2)
        #  (imin + s/2 - 1, jmin + s/2 - 1). We can distinguish these two cases by
        #  looking at the low bit of "i" or "j". In the first case the low bit is
        #  zero, unless s == 2 (i.e. the level just above leaf cells) in which case
        #  the low bit is one.
        #
        #  The following calculation converts (i,j) to the (si,ti) coordinates of
        #  the cell center. (We need to multiply the coordinates by a factor of 2
        #  so that the center of leaf cells can be represented exactly.)
        i = 0
        j = 0
        i, j, face = self.toFaceIJOrientation(i, j, None)
        delta = 1 if self.isLeaf() else (2 if (((i ^ (long(self.id) >> 2)) & 1) != 0) else 0)
        si = (i << 1) + delta - self.MAX_SIZE
        ti = (j << 1) + delta - self.MAX_SIZE
        return self.faceSiTiToXYZ(face, si, ti)

    def toLatLng(self):
        """Return the S2LatLng corresponding to the center of the given cell."""
        return S2LatLng(self.toPointRaw())

    def isValid(self):
        """Return true if id() represents a valid cell."""
        return self.face() < self.NUM_FACES and ((self.lowestOnBit() & (0x1555555555555555L)) != 0)

    def face(self):
        """Which cube face this cell belongs to, in the range 0..5."""
        return int(self.id >> self.POS_BITS)

    #
    # The position of the cell center along the Hilbert curve over this face, in
    # the range 0..(2**kPosBits-1).
    #
    def pos(self):
        """ generated source for method pos """
        return (self.id & (self.MAX_UNSIGNED >> self.FACE_BITS))

    def level(self):
        """Return the subdivision level of the cell (range 0..MAX_LEVEL)."""
        #  Fast path for leaf cells.
        if self.isLeaf():
            return self.MAX_LEVEL
        x = int(self.id)
        level = -1
        if x != 0:
            level += 16
        else:
            x = int(self.id >> 32)
        #  We only need to look at even-numbered bits to determine the
        #  level of a valid cell id.
        x &= -x
        #  Get lowest bit.
        if (x & 0x00005555) != 0:
            level += 8
        if (x & 0x00550055) != 0:
            level += 4
        if (x & 0x05050505) != 0:
            level += 2
        if (x & 0x11111111) != 0:
            level += 1
        #  assert (level >= 0 && level <= MAX_LEVEL);
        return level

    def isLeaf(self):
        """
        Return true if this is a leaf cell (more efficient than checking whether
        level() == MAX_LEVEL).
        """
        return (int(self.id) & 1) != 0

    def isFace(self):
        """
        Return true if this is a top-level face cell (more efficient than checking
        whether level() == 0).
        """
        return (self.id & (self.lowestOnBitForLevel(0) - 1)) == 0

    #  Methods that return the range of cell ids that are contained
    #  within this cell (including itself). The range is *inclusive*
    #  (i.e. test using >= and <=) and the return values of both
    #  methods are valid leaf cell ids.
    #
    #  These methods should not be used for iteration. If you want to
    #  iterate through all the leaf cells, call child_begin(MAX_LEVEL) and
    #  child_end(MAX_LEVEL) instead.
    #
    #  It would in fact be error-prone to define a range_end() method,
    #  because (range_max().id() + 1) is not always a valid cell id, and the
    #  iterator would need to be tested using "<" rather that the usual "!=".
    def rangeMin(self):
        """ generated source for method rangeMin """
        return S2CellId(self.id - (self.lowestOnBit() - 1))

    def rangeMax(self):
        """ generated source for method rangeMax """
        return S2CellId(self.id + (self.lowestOnBit() - 1))

    #  Return true if the given cell is contained within this one.
    def contains(self, other):
        """ generated source for method contains """
        #  assert (isValid() && other.isValid());
        return other.greaterOrEquals(self.rangeMin()) and other.lessOrEquals(self.rangeMax())

    #  Return true if the given cell intersects this one.
    def intersects(self, other):
        """ generated source for method intersects """
        #  assert (isValid() && other.isValid());
        return other.rangeMin().lessOrEquals(self.rangeMax()) and other.rangeMax().greaterOrEquals(self.rangeMin())

    #
    # Return the cell at the previous level or at the given level (which must be
    # less than or equal to the current level).
    #
    def parent(self, level=0):
        """ generated source for method parent_0 """
        #  assert (isValid() && level >= 0 && level <= this.level());
        if not level:
            # optimization from original code; may not be useful
            newLsb = self.lowestOnBit() << 2
        else:
            newLsb = self.lowestOnBitForLevel(level)
        return S2CellId((self.id & -newLsb) | newLsb)

    def childBegin(self, level = None):
        """ generated source for method childBegin """
        if level is None:
            #  assert (isValid() && level() < MAX_LEVEL);
            oldLsb = self.lowestOnBit()
            return S2CellId(self.id - oldLsb + (oldLsb >> 2))
        else:
            #  assert (isValid() && level >= this.level() && level <= MAX_LEVEL);
            return S2CellId(self.id - self.lowestOnBit() + self.lowestOnBitForLevel(level))

    def childEnd(self, level = None):
        """ generated source for method childEnd """
        if level is None:
            #  assert (isValid() && level() < MAX_LEVEL);
            oldLsb = self.lowestOnBit()
            return S2CellId(self.id + oldLsb + (oldLsb >> 2))
        else:
            #  assert (isValid() && level >= this.level() && level <= MAX_LEVEL);
            return S2CellId(self.id + self.lowestOnBit() + self.lowestOnBitForLevel(level))

    #  Iterator-style methods for traversing the immediate children of a cell or
    #  all of the children at a given level (greater than or equal to the current
    #  level). Note that the end value is exclusive, just like standard STL
    #  iterators, and may not even be a valid cell id. You should iterate using
    #  code like this:
    #
    #  for(S2CellId c = id.childBegin(); !c == id.childEnd(); c = c.next())
    #  ...
    #
    #  The convention for advancing the iterator is "c = c.next()", so be sure
    #  to use 'equals()' in the loop guard, or compare 64-bit cell id's,
    #  rather than "c != id.childEnd()".
    #
    # Return the next cell at the same level along the Hilbert curve. Works
    # correctly when advancing from one face to the next, but does *not* wrap
    # around from the last face to the first or vice versa.
    #
    def next(self):
        """ generated source for method next """
        return S2CellId(self.id + (self.lowestOnBit() << 1))

    #
    # Return the previous cell at the same level along the Hilbert curve. Works
    # correctly when advancing from one face to the next, but does *not* wrap
    # around from the last face to the first or vice versa.
    #
    def prev(self):
        """ generated source for method prev """
        return S2CellId(self.id - (self.lowestOnBit() << 1))

    #
    # Like next(), but wraps around from the last face to the first and vice
    # versa. Should *not* be used for iteration in conjunction with
    # child_begin(), child_end(), Begin(), or End().
    #
    def nextWrap(self):
        """ generated source for method nextWrap """
        n = self.next()
        if n.id < self.WRAP_OFFSET:
            return n
        return S2CellId(n.id - self.WRAP_OFFSET)

    #
    # Like prev(), but wraps around from the last face to the first and vice
    # versa. Should *not* be used for iteration in conjunction with
    # child_begin(), child_end(), Begin(), or End().
    #
    def prevWrap(self):
        """ generated source for method prevWrap """
        p = self.prev()
        if p.id < self.WRAP_OFFSET:
            return p
        return S2CellId(p.id + self.WRAP_OFFSET)

    @classmethod
    def begin(cls, level):
        """ generated source for method begin """
        return cls.fromFacePosLevel(0, 0, 0).childBegin(level)

    @classmethod
    def end(cls, level):
        """ generated source for method end """
        return cls.fromFacePosLevel(5, 0, 0).childEnd(level)


    # TODO: to/from token methods

    # TODO: neighbor methods

    #
    # Append all neighbors of this cell at the given level to "output". Two cells
    # X and Y are neighbors if their boundaries intersect but their interiors do
    # not. In particular, two cells that intersect at a single point are
    # neighbors.
    #
    # Requires: nbr_level >= this->level(). Note that for cells adjacent to a
    # face vertex, the same neighbor may be appended more than once.
    #
    def getAllNeighbors(self, nbrLevel):
        """ generated source for method getAllNeighbors """
        i = 0
        j = 0
        output = set()
        i, j, face = self.toFaceIJOrientation(i, j, None)
        #  Find the coordinates of the lower left-hand leaf cell. We need to
        #  normalize (i,j) to a known position within the cell because nbr_level
        #  may be larger than this cell's level.
        size = 1 << (self.MAX_LEVEL - self.level())
        i = i & -size
        j = j & -size
        nbrSize = 1 << (self.MAX_LEVEL - nbrLevel)
        #  assert (nbrSize <= size);
        #  We compute the N-S, E-W, and diagonal neighbors in one pass.
        #  The loop test is at the end of the loop to avoid 32-bit overflow.
        k = -nbrSize
        while True:
            if k < 0:
                sameFace = (j + k >= 0)
            elif k >= size:
                sameFace = (j + k < self.MAX_SIZE)
            else:
                sameFace = True
                #  North and South neighbors.
                output.add(self.fromFaceIJSame(face, i + k, j - nbrSize, j - size >= 0).parent(nbrLevel))
                output.add(self.fromFaceIJSame(face, i + k, j + size, j + size < self.MAX_SIZE).parent(nbrLevel))
            #  East, West, and Diagonal neighbors.
            output.add(self.fromFaceIJSame(face, i - nbrSize, j + k, sameFace and i - size >= 0).parent(nbrLevel))
            output.add(self.fromFaceIJSame(face, i + size, j + k, sameFace and i + size < self.MAX_SIZE).parent(nbrLevel))
            if k >= size:
                break
            k += nbrSize
        return output

    #  ///////////////////////////////////////////////////////////////////
    #  Low-level methods.
    #
    # Return a leaf cell given its cube face (range 0..5) and i- and
    # j-coordinates (see s2.h).
    #
    @classmethod
    def fromFaceIJ(cls, face, i, j):
        """ generated source for method fromFaceIJ """
        #  Optimization notes:
        #  - Non-overlapping bit fields can be combined with either "+" or "|".
        #  Generally "+" seems to produce better code, but not always.
        #  gcc doesn't have very good code generation for 64-bit operations.
        #  We optimize this by computing the result as two 32-bit integers
        #  and combining them at the end. Declaring the result as an array
        #  rather than local variables helps the compiler to do a better job
        #  of register allocation as well. Note that the two 32-bits halves
        #  get shifted one bit to the left when they are combined.
        n = [0, face << (cls.POS_BITS - 33)]
        #  Alternating faces have opposite Hilbert curve orientations; this
        #  is necessary in order for all faces to have a right-handed
        #  coordinate system.
        bits = (face & cls.SWAP_MASK)
        #  Each iteration maps 4 bits of "i" and "j" into 8 bits of the Hilbert
        #  curve position. The lookup table transforms a 10-bit key of the form
        #  "iiiijjjjoo" to a 10-bit value of the form "ppppppppoo", where the
        #  letters [ijpo] denote bits of "i", "j", Hilbert curve position, and
        #  Hilbert curve orientation respectively.
        k = 7
        while k >= 0:
            bits = cls.getBits(n, i, j, k, bits)
            k -= 1
        s = S2CellId((((n[1] << 32) + n[0]) << 1) + 1)
        return s

    @classmethod
    def getBits(cls, n, i, j, k, bits):
        """ generated source for method getBits """
        mask = (1 << cls.LOOKUP_BITS) - 1
        bits += (((i >> (k * cls.LOOKUP_BITS)) & mask) << (cls.LOOKUP_BITS + 2))
        bits += (((j >> (k * cls.LOOKUP_BITS)) & mask) << 2)
        bits = cls.LOOKUP_POS[bits]
        n[k >> 2] |= (((long(bits)) >> 2) << ((k & 3) * 2 * cls.LOOKUP_BITS))
        bits &= (cls.SWAP_MASK | cls.INVERT_MASK)
        return bits

    #
    # Return the (face, i, j) coordinates for the leaf cell corresponding to this
    # cell id. Since cells are represented by the Hilbert curve position at the
    # center of the cell, the returned (i,j) for non-leaf cells will be a leaf
    # cell adjacent to the cell center. If "orientation" is non-NULL, also return
    # the Hilbert curve orientation for the current cell.
    #
    def toFaceIJOrientation(self, pi, pj, orientation):
        """ generated source for method toFaceIJOrientation """
        #  print "Entering toFaceIjorientation";
        face = self.face()
        bits = (face & self.SWAP_MASK)
        #  print "face = " + face + " bits = " + bits;
        #  Each iteration maps 8 bits of the Hilbert curve position into
        #  4 bits of "i" and "j". The lookup table transforms a key of the
        #  form "ppppppppoo" to a value of the form "iiiijjjjoo", where the
        #  letters [ijpo] represents bits of "i", "j", the Hilbert curve
        #  position, and the Hilbert curve orientation respectively.
        #
        #  On the first iteration we need to be careful to clear out the bits
        #  representing the cube face.
        k = 7
        while k >= 0:
            pi, pj, bits = self.getBits1(pi, pj, k, bits)
            #  print "pi = " + pi + " pj= " + pj + " bits = " + bits;
            k -= 1
        if orientation != None:
            #  The position of a non-leaf cell at level "n" consists of a prefix of
            #  2*n bits that identifies the cell, followed by a suffix of
            #  2*(MAX_LEVEL-n)+1 bits of the form 10*. If n==MAX_LEVEL, the suffix is
            #  just "1" and has no effect. Otherwise, it consists of "10", followed
            #  by (MAX_LEVEL-n-1) repetitions of "00", followed by "0". The "10" has
            #  no effect, while each occurrence of "00" has the effect of reversing
            #  the kSwapMask bit.
            #  assert (S2.POS_TO_ORIENTATION[2] == 0);
            #  assert (S2.POS_TO_ORIENTATION[0] == S2.SWAP_MASK);
            if (lowestOnBit() & 0x1111111111111110L) != 0:
                bits ^= S2.SWAP_MASK
            orientation.setValue(bits)
        return (pi, pj, face)

    def getBits1(self, i, j, k, bits):
        """ generated source for method getBits1 """
        nbits = (self.MAX_LEVEL - 7 * self.LOOKUP_BITS) if (k == 7) else self.LOOKUP_BITS
        bits += ((int((self.id >> (k * 2 * self.LOOKUP_BITS + 1))) & ((1 << (2 * nbits)) - 1))) << 2
        #
        # print "id is: " + id_; System.out.println("bits is " +
        # bits); print "lookup_ij[bits] is " + lookup_ij[bits];
        #
        bits = self.LOOKUP_IJ[bits]
        i += ((bits >> (self.LOOKUP_BITS + 2)) << (k * self.LOOKUP_BITS))
        #
        # print "left is " + ((bits >> 2) & ((1 << kLookupBits -
        # 1))); print "right is " + (k * kLookupBits);
        # print "j is: " + j.intValue(); System.out.println("addition
        # is: " + ((((bits >> 2) & ((1 << kLookupBits) - 1))) << (k *
        # kLookupBits)));
        #
        j += ((((bits >> 2) & ((1 << self.LOOKUP_BITS) - 1))) << (k * self.LOOKUP_BITS))
        bits &= (self.SWAP_MASK | self.INVERT_MASK)
        return (i, j, bits)

    def lowestOnBit(self):
        """
        Return the lowest-numbered bit that is on for this cell id, which is equal
        to (uint64(1) << (2 * (MAX_LEVEL - level))). So for example, a.lsb() <=
        b.lsb() if and only if a.level() >= b.level(), but the first test is more
        efficient.
        """
        return (self.id & -self.id)

    @classmethod
    def lowestOnBitForLevel(cls, level):
        """Return the lowest-numbered bit that is on for cells at the given level."""
        return (1 << (2 * (cls.MAX_LEVEL - level))) & cls.MAX_UNSIGNED
    #
    # Return the i- or j-index of the leaf cell containing the given s- or
    # t-value.
    #
    @classmethod
    def stToIJ(cls, s):
        """ generated source for method stToIJ """
        #  Converting from floating-point to integers via static_cast is very slow
        #  on Intel processors because it requires changing the rounding mode.
        #  Rounding to the nearest integer using FastIntRound() is much faster.
        m = cls.MAX_SIZE / 2
        #  scaling multiplier
        return int(max(0, min(2 * m - 1, round(m * s + (m - 0.5)))))

    #
    # Convert (face, si, ti) coordinates (see s2.h) to a direction vector (not
    # necessarily unit length).
    #
    @classmethod
    def faceSiTiToXYZ(cls, face, si, ti):
        """ generated source for method faceSiTiToXYZ """
        kScale = 1.0 / cls.MAX_SIZE
        u = S2Projections.stToUV(kScale * si)
        v = S2Projections.stToUV(kScale * ti)
        return S2Projections.faceUvToXyz(face, u, v)

    #
    # Given (i, j) coordinates that may be out of bounds, normalize them by
    # returning the corresponding neighbor cell on an adjacent face.
    #
    @classmethod
    def fromFaceIJWrap(cls, face, i, j):
        """ generated source for method fromFaceIJWrap """
        #  Convert i and j to the coordinates of a leaf cell just beyond the
        #  boundary of this face. This prevents 32-bit overflow in the case
        #  of finding the neighbors of a face cell, and also means that we
        #  don't need to worry about the distinction between (s,t) and (u,v).
        i = max(-1, min(cls.MAX_SIZE, i))
        j = max(-1, min(cls.MAX_SIZE, j))
        #  Find the (s,t) coordinates corresponding to (i,j). At least one
        #  of these coordinates will be just outside the range [0, 1].
        kScale = 1.0 / cls.MAX_SIZE
        s = kScale * ((i << 1) + 1 - cls.MAX_SIZE)
        t = kScale * ((j << 1) + 1 - cls.MAX_SIZE)
        #  Find the leaf cell coordinates on the adjacent face, and convert
        #  them to a cell id at the appropriate level.
        p = S2Projections.faceUvToXyz(face, s, t)
        face = S2Projections.xyzToFace(p)
        st = S2Projections.validFaceXyzToUv(face, p)
        return cls.fromFaceIJ(face, cls.stToIJ(st[0]), cls.stToIJ(st[1]))

    #
    # Public helper function that calls FromFaceIJ if sameFace is true, or
    # FromFaceIJWrap if sameFace is false.
    #
    @classmethod
    def fromFaceIJSame(cls, face, i, j, sameFace):
        """ generated source for method fromFaceIJSame """
        if sameFace:
            return cls.fromFaceIJ(face, i, j)
        else:
            return cls.fromFaceIJWrap(face, i, j)

    def __eq__(self, that):
        if not isinstance(that, S2CellId):
            return False
        return self.id == that.id

    def __ne__(self, that):
        return self.id != that.id

    def __lt__(self, that):
        return self.id < that.id

    def __le__(self, that):
        return self.id <= that.id

    def __gt__(self, that):
        return self.id > that.id

    def __ge__(self, that):
        return self.id >= that.id

    @classmethod
    def initLookupCell(cls, level, i, j, origOrientation, pos, orientation):
        """ generated source for method initLookupCell """
        if level == cls.LOOKUP_BITS:
            ij = (i << cls.LOOKUP_BITS) + j
            cls.LOOKUP_POS[(ij << 2) + origOrientation] = (pos << 2) + orientation
            cls.LOOKUP_IJ[(pos << 2) + origOrientation] = (ij << 2) + orientation
        else:
            level += 1
            i <<= 1
            j <<= 1
            pos <<= 2
            subPos = 0
            #  Initialize each sub-cell recursively.
            while subPos < 4:
                ij = S2.posToIJ(orientation, subPos)
                orientationMask = S2.posToOrientation(subPos)
                cls.initLookupCell(level, i + (ij >> 1), j + (ij & 1), origOrientation, pos + subPos, orientation ^ orientationMask)
                subPos += 1

    def __hash__(self):
        """ generated source for method hashCode """
        return long((self.id >> 32) + self.id)

    def __str__(self):
        return "S2CellId<face=%d, pos=%x, level=%d>" % (self.face(), self.pos(), self.level())

S2CellId.initLookupCell(0, 0, 0, 0, 0, 0)
S2CellId.initLookupCell(0, 0, 0, S2CellId.SWAP_MASK, 0, S2CellId.SWAP_MASK)
S2CellId.initLookupCell(0, 0, 0, S2CellId.INVERT_MASK, 0, S2CellId.INVERT_MASK)
S2CellId.initLookupCell(0, 0, 0, S2CellId.SWAP_MASK|S2CellId.INVERT_MASK, 0, S2CellId.SWAP_MASK|S2CellId.INVERT_MASK)


class S2CellUnion(object):
    """
    An S2CellUnion is a region consisting of cells of various sizes. Typically a
    cell union is used to approximate some other shape. There is a tradeoff
    between the accuracy of the approximation and how many cells are used. Unlike
    polygons, cells have a fixed hierarchical structure. This makes them more
    suitable for optimizations based on preprocessing.
    """

    def __init__(self):
        """ generated source for method __init__ """
        super(S2CellUnion, self).__init__()
        #  The CellIds that form the Union
        self.cellIds = []

    def initFromCellIds(self, cellIds):
        """ generated source for method initFromCellIds """
        self.initRawCellIds(cellIds)
        self.normalize()

    #
    # Populates a cell union with the given S2CellIds or 64-bit cells ids, and
    # then calls Normalize(). The InitSwap() version takes ownership of the
    # vector data without copying and clears the given vector. These methods may
    # be called multiple times.
    #
    def initFromIds(self, cellIds):
        """ generated source for method initFromIds """
        self.initRawIds(cellIds)
        self.normalize()

    def initSwap(self, cellIds):
        """ generated source for method initSwap """
        self.initRawSwap(cellIds)
        self.normalize()

    def initRawCellIds(self, cellIds):
        """ generated source for method initRawCellIds """
        self.cellIds = cellIds

    def initRawIds(self, cellIds):
        """ generated source for method initRawIds """
        self.cellIds = [S2CellId(id) for id in cellIds]

    #
    # Like Init(), but does not call Normalize(). The cell union *must* be
    # normalized before doing any calculations with it, so it is the caller's
    # responsibility to make sure that the input is normalized. This method is
    # useful when converting cell unions to another representation and back.
    # These methods may be called multiple times.
    #
    def initRawSwap(self, cellIds):
        """ generated source for method initRawSwap """
        self.cellIds = list(cellIds)

    def size(self):
        """ generated source for method size """
        return len(self.cellIds)

    #  Convenience methods for accessing the individual cell ids.
    def cellId(self, i):
        """ generated source for method cellId """
        return self.cellIds[i]

    #  Enable iteration over the union's cells.
    def __iter__(self):
        """ generated source for method iterator """
        return iter(self.cellIds)

    #
    # Replaces "output" with an expanded version of the cell union where any
    # cells whose level is less than "min_level" or where (level - min_level) is
    # not a multiple of "level_mod" are replaced by their children, until either
    # both of these conditions are satisfied or the maximum level is reached.
    #
    #  This method allows a covering generated by S2RegionCoverer using
    # min_level() or level_mod() constraints to be stored as a normalized cell
    # union (which allows various geometric computations to be done) and then
    # converted back to the original list of cell ids that satisfies the desired
    # constraints.
    #
    def denormalize(self, minLevel, levelMod):
        """ generated source for method denormalize """
        #  assert (minLevel >= 0 && minLevel <= S2CellId.MAX_LEVEL);
        #  assert (levelMod >= 1 && levelMod <= 3);
        output = []
        for id in self:
            level = id.level()
            newLevel = max(minLevel, level)
            if levelMod > 1:
                #  Round up so that (new_level - min_level) is a multiple of level_mod.
                #  (Note that S2CellId::kMaxLevel is a multiple of 1, 2, and 3.)
                newLevel += (S2CellId.MAX_LEVEL - (newLevel - minLevel)) % levelMod
                newLevel = min(S2CellId.MAX_LEVEL, newLevel)
            if newLevel == level:
                output.append(id)
            else:
                end = id.childEnd(newLevel)
                id = id.childBegin(newLevel)
                while not id == end:
                    output.append(id)
                    id = id.next()

    #
    # Return true if the cell union contains the given cell id. Containment is
    # defined with respect to regions, e.g. a cell contains its 4 children. This
    # is a fast operation (logarithmic in the size of the cell union).
    #
    def contains(self, id):
        """ generated source for method contains """
        #  This function requires that Normalize has been called first.
        #
        #  This is an exact test. Each cell occupies a linear span of the S2
        #  space-filling curve, and the cell id is simply the position at the center
        #  of this span. The cell union ids are sorted in increasing order along
        #  the space-filling curve. So we simply find the pair of cell ids that
        #  surround the given cell id (using binary search). There is containment
        #  if and only if one of these two cell ids contains this cell.
        if isinstance(id, S2CellUnion):
            for x in id:
                if not self.contains(x):
                    return False
            return True
        elif isinstance(id, S2Cell):
            return self.contains(id.id)

        try:
            pos = self.cellIds.index(id)
        except:
            for pos in xrange(len(self.cellIds)):
                if self.cellIds[pos] > id:
                    break
            pos = -pos
        if pos < 0:
            pos = -pos - 1
        if pos < len(self.cellIds) and self.cellIds.get(pos).rangeMin() <= id:
            return True
        return pos != 0 and self.cellIds.get(pos - 1).rangeMax() >= id

    def normalize(self):
        """ generated source for method normalize """
        output = list()
        self.cellIds.sort()
        for id in self:
            size = len(output)
            if output and output[size - 1].contains(id):
                continue
            while output and id.contains(output[-1]):
                del output[-1]
            while len(output) >= 3:
                size = len(output)
                if (output[size - 3].id ^ output[size - 2].id ^ output[self.size - 1].id) != id.id:
                    break
                mask = id.lowestOnBit() << 1
                mask = ~(mask + (mask << 1))
                idMasked = (id.id & mask)
                if (output[self.size - 3].id & mask) != idMasked or (output[self.size - 2].id & mask) != idMasked or (output[self.size - 1].id & mask) != idMasked or id.isFace():
                    break
                del output[size - 1]
                del output[size - 2]
                del output[size - 3]
                id = id.parent()
            output.append(id)
        if len(output) < len(self):
            self.initRawSwap(output)
            return True
        return False


class S2LatLng(object):
    """
    This class represents a point on the unit sphere as a pair of
    latitude-longitude coordinates. Like the rest of the "geometry" package, the
    intent is to represent spherical geometry as a mathematical abstraction, so
    functions that are specifically related to the Earth's geometry (e.g.
    easting/northing conversions) should be put elsewhere.
    """

    #
    # Approximate "effective" radius of the Earth in meters.
    #
    EARTH_RADIUS_METERS = 6367000.0

    #  The center point the lat/lng coordinate system.
    #CENTER = S2LatLng(0.0, 0.0)

    @classmethod
    def fromRadians(cls, latRadians, lngRadians):
        """ generated source for method fromRadians """
        return cls(latRadians, lngRadians)

    @classmethod
    def fromDegrees(cls, latDegrees, lngDegrees):
        """ generated source for method fromDegrees """
        return cls(math.radians(latDegrees), math.radians(lngDegrees))

    @classmethod
    def fromE6(cls, latE6, lngE6):
        """ generated source for method fromE6 """
        return cls.fromDegrees(latE6 / 1e6, lngE6 / 1e6)

    def __init__(self, latRadians=0.0, lngRadians=0.0):
        """ generated source for method __init__ """
        if isinstance(latRadians, S2Point):
            p = latRadians
            self.latRadians = math.atan2(p.z, math.sqrt(p.x * p.x + p.y * p.y))
            self.lngRadians = math.atan2(p.y, p.x)
        else:
            self.latRadians = latRadians
            self.lngRadians = lngRadians

    #  Returns the latitude of this point as degrees.
    def latDegrees(self):
        """ generated source for method latDegrees """
        return math.degrees(self.latRadians)

    #  Returns the longitude of this point as degrees.
    def lngDegrees(self):
        """ generated source for method lngDegrees """
        return math.degrees(self.lngRadians)

    #
    # Return true if the latitude is between -90 and 90 degrees inclusive and the
    # longitude is between -180 and 180 degrees inclusive.
    #
    def isValid(self):
        """ generated source for method isValid """
        return math.fabs(self.latRadians) <= S2.M_PI_2 and math.fabs(self.lngRadians) <= S2.M_PI

    #
    # Returns a new S2LatLng based on this instance for which {@link #isValid()}
    # will be {@code true}.
    # <ul>
    # <li>Latitude is clipped to the range {@code [-90, 90]}
    # <li>Longitude is normalized to be in the range {@code [-180, 180]}
    # </ul>
    # <p>If the current point is valid then the returned point will have the same
    # coordinates.
    #
    def normalized(self):
        """ generated source for method normalized """
        lng = (self.lngRadians % (2 * S2.M_PI))
        if lng >= S2.M_PI:
            lng -= 2 * S2.M_PI
        return S2LatLng(max(-S2.M_PI_2, min(S2.M_PI_2, self.latRadians)), lng)

    #  Convert an S2LatLng to the equivalent unit-length vector (S2Point).
    def toPoint(self):
        """ generated source for method toPoint """
        phi = self.latRadians
        theta = self.lngRadians
        cosphi = math.cos(phi)
        return S2Point(math.cos(theta) * cosphi, math.sin(theta) * cosphi, math.sin(phi))

    #
    # Return the distance (measured along the surface of the sphere) to the given
    # point.
    #
    def getDistance(self, o, radius = None):
        """ generated source for method getDistance """
        #  This implements the Haversine formula, which is numerically stable for
        #  small distances but only gets about 8 digits of precision for very large
        #  distances (e.g. antipodal points). Note that 8 digits is still accurate
        #  to within about 10cm for a sphere the size of the Earth.
        #
        #  This could be fixed with another sin() and cos() below, but at that point
        #  you might as well just convert both arguments to S2Points and compute the
        #  distance that way (which gives about 15 digits of accuracy for all
        #  distances).
        lat1 = self.latRadians
        lat2 = o.latRadians
        lng1 = self.lngRadians
        lng2 = o.lngRadians
        dlat = math.sin(0.5 * (lat2 - lat1))
        dlng = math.sin(0.5 * (lng2 - lng1))
        x = dlat * dlat + dlng * dlng * math.cos(lat1) * math.cos(lat2)
        distRads = 2 * math.atan2(math.sqrt(x), math.sqrt(max(0.0, 1.0 - x)))
        if radius is None:
            return distRads
        return distRads * radius

    #
    # Returns the surface distance to the given point assuming the default Earth
    # radius of {@link #EARTH_RADIUS_METERS}.
    #
    def getEarthDistance(self, o):
        """ generated source for method getEarthDistance """
        return self.getDistance(o, self.EARTH_RADIUS_METERS)

    def __str__(self):
        return "S2LatLng<lat=%f, lng=%f>" % (self.latDegrees(), self.lngDegrees())


class S2Point(object):
    """
    An S2Point represents a point on the unit sphere as a 3D vector. Usually
    points are normalized to be unit length, but some methods do not require
    this.
    """

    def __init__(self, x=0, y=0, z=0):
        """ generated source for method __init__ """
        super(S2Point, self).__init__()
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def minus(cls, p1, p2):
        """ generated source for method minus """
        return sub(p1, p2)

    @classmethod
    def neg(cls, p):
        """ generated source for method neg """
        return S2Point(-p.x, -p.y, -p.z)

    def norm2(self):
        """ generated source for method norm2 """
        return self.x * self.x + self.y * self.y + self.z * self.z

    def norm(self):
        """ generated source for method norm """
        return math.sqrt(self.norm2())

    @classmethod
    def crossProd(cls, p1, p2):
        """ generated source for method crossProd """
        return S2Point(p1.y * p2.z - p1.z * p2.y, p1.z * p2.x - p1.x * p2.z, p1.x * p2.y - p1.y * p2.x)

    @classmethod
    def add(cls, p1, p2):
        """ generated source for method add """
        return S2Point(p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

    @classmethod
    def sub(cls, p1, p2):
        """ generated source for method sub """
        return S2Point(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)

    def dotProd(self, that):
        """ generated source for method dotProd """
        return self.x * that.x + self.y * that.y + self.z * that.z

    @classmethod
    def mul(cls, p, m):
        """ generated source for method mul """
        return S2Point(m * p.x, m * p.y, m * p.z)

    @classmethod
    def div(cls, p, m):
        """ generated source for method div """
        return S2Point(p.x / m, p.y / m, p.z / m)

    #  return a vector orthogonal to this one
    def ortho(self):
        """ generated source for method ortho """
        k = self.largestAbsComponent()
        temp = S2Point()
        if k == 1:
            temp = S2Point(1, 0, 0)
        elif k == 2:
            temp = S2Point(0, 1, 0)
        else:
            temp = S2Point(0, 0, 1)
        return S2Point.normalize(self.crossProd(self, temp))

    #  Return the index of the largest component fabs
    def largestAbsComponent(self):
        """ generated source for method largestAbsComponent """
        temp = self.fabs(self)
        if temp.x > temp.y:
            if temp.x > temp.z:
                return 0
            else:
                return 2
        else:
            if temp.y > temp.z:
                return 1
            else:
                return 2

    @classmethod
    def fabs(cls, p):
        """ generated source for method fabs """
        return S2Point(math.fabs(p.x), math.fabs(p.y), math.fabs(p.z))

    @classmethod
    def normalize(cls, p):
        """ generated source for method normalize """
        norm = p.norm()
        if norm != 0:
            norm = 1.0 / norm
        return S2Point.mul(p, norm)

    def get(self, axis):
        """ generated source for method get """
        return self.x if (axis == 0) else (self.y if (axis == 1) else self.z)

    #  Return the angle between two vectors in radians
    def angle(self, va):
        """ generated source for method angle """
        return math.atan2(self.crossProd(self, va).norm(), self.dotProd(va))

    def __str__(self):
        """ generated source for method toString """
        return "S2Point(%g, %g, %g)" % (self.x, self.y, self.z)

    def toDegreesString(self):
        """ generated source for method toDegreesString """
        s2LatLng = S2LatLng(self)
        return "(" + s2LatLng.latDegrees() + ", " + s2LatLng.lngDegrees() + ")"


#
# This class specifies the details of how the cube faces are projected onto the
# unit sphere. This includes getting the face ordering and orientation correct
# so that sequentially increasing cell ids follow a continuous space-filling
# curve over the entire sphere, and defining the transformation from cell-space
# to cube-space (see s2.h) in order to make the cells more uniform in size.
#
#
# We have implemented three different projections from cell-space (s,t) to
# cube-space (u,v): linear, quadratic, and tangent. They have the following
# tradeoffs:
#
# Linear - This is the fastest transformation, but also produces the least
# uniform cell sizes. Cell areas vary by a factor of about 5.2, with the
# largest cells at the center of each face and the smallest cells in the
# corners.
#
# Tangent - Transforming the coordinates via atan() makes the cell sizes more
# uniform. The areas vary by a maximum ratio of 1.4 as opposed to a maximum
# ratio of 5.2. However, each call to atan() is about as expensive as all of
# the other calculations combined when converting from points to cell ids, i.e.
# it reduces performance by a factor of 3.
#
# Quadratic - This is an approximation of the tangent projection that is much
# faster and produces cells that are almost as uniform in size. It is about 3
# times faster than the tangent projection for converting cell ids to points,
# and 2 times faster for converting points to cell ids. Cell areas vary by a
# maximum ratio of about 2.1.
#
# Here is a table comparing the cell uniformity using each projection. "Area
# ratio" is the maximum ratio over all subdivision levels of the largest cell
# area to the smallest cell area at that level, "edge ratio" is the maximum
# ratio of the longest edge of any cell to the shortest edge of any cell at the
# same level, and "diag ratio" is the ratio of the longest diagonal of any cell
# to the shortest diagonal of any cell at the same level. "ToPoint" and
# "FromPoint" are the times in microseconds required to convert cell ids to and
# from points (unit vectors) respectively.
#
#            Area  Edge  Diag  ToPoint FromPoint
#            Ratio Ratio Ratio  (microseconds)
# -------------------------------------------------------
# Linear:    5.200 2.117 2.959  0.103    0.123
# Tangent:   1.414 1.414 1.704  0.290    0.306
# Quadratic: 2.082 1.802 1.932  0.116    0.161
#
# The worst-case cell aspect ratios are about the same with all three
# projections. The maximum ratio of the longest edge to the shortest edge
# within the same cell is about 1.4 and the maximum ratio of the diagonals
# within the same cell is about 1.7.
class S2Projections(object):

    @classmethod
    def stToUV(cls, s):
        """ generated source for method stToUV """
        if s >= 0:
            return (1 / 3.) * ((1 + s) * (1 + s) - 1)
        else:
            return (1 / 3.) * (1 - (1 - s) * (1 - s))

    @classmethod
    def uvToST(cls, u):
        """ generated source for method uvToST """
        if u >= 0:
            return math.sqrt(1 + 3 * u) - 1
        else:
            return 1 - math.sqrt(1 - 3 * u)

    #
    # Convert (face, u, v) coordinates to a direction vector (not necessarily
    # unit length).
    #
    @classmethod
    def faceUvToXyz(cls, face, u, v):
        """ generated source for method faceUvToXyz """
        if face==0:
            return S2Point(1, u, v)
        elif face==1:
            return S2Point(-u, 1, v)
        elif face==2:
            return S2Point(-u, -v, 1)
        elif face==3:
            return S2Point(-1, -v, -u)
        elif face==4:
            return S2Point(v, -1, -u)
        else:
            return S2Point(v, u, -1)

    @classmethod
    def validFaceXyzToUv(cls, face, p):
        """ generated source for method validFaceXyzToUv """
        #  assert (p.dotProd(faceUvToXyz(face, 0, 0)) > 0);
        pu = float()
        pv = float()
        if face==0:
            pu = p.y / p.x
            pv = p.z / p.x
        elif face==1:
            pu = -p.x / p.y
            pv = p.z / p.y
        elif face==2:
            pu = -p.x / p.z
            pv = -p.y / p.z
        elif face==3:
            pu = p.z / p.x
            pv = p.y / p.x
        elif face==4:
            pu = p.z / p.y
            pv = -p.x / p.y
        else:
            pu = -p.y / p.z
            pv = -p.x / p.z
        return (pu, pv)

    @classmethod
    def xyzToFace(cls, p):
        """ generated source for method xyzToFace """
        face = p.largestAbsComponent()
        if p.get(face) < 0:
            face += 3
        return face

    @classmethod
    def faceXyzToUv(cls, face, p):
        """ generated source for method faceXyzToUv """
        if face < 3:
            if p.get(face) <= 0:
                return None
        else:
            if p.get(face - 3) >= 0:
                return None
        return cls.validFaceXyzToUv(face, p)

    @classmethod
    def getUNorm(cls, face, u):
        """ generated source for method getUNorm """
        if face==0:
            return S2Point(u, -1, 0)
        elif face==1:
            return S2Point(1, u, 0)
        elif face==2:
            return S2Point(1, 0, u)
        elif face==3:
            return S2Point(-u, 0, 1)
        elif face==4:
            return S2Point(0, -u, 1)
        else:
            return S2Point(0, -1, -u)

    @classmethod
    def getVNorm(cls, face, v):
        """ generated source for method getVNorm """
        if face==0:
            return S2Point(-v, 0, 1)
        elif face==1:
            return S2Point(0, -v, 1)
        elif face==2:
            return S2Point(0, -1, -v)
        elif face==3:
            return S2Point(v, -1, 0)
        elif face==4:
            return S2Point(1, v, 0)
        else:
            return S2Point(1, 0, v)

    @classmethod
    def getNorm(cls, face):
        """ generated source for method getNorm """
        return cls.faceUvToXyz(face, 0, 0)

    @classmethod
    def getUAxis(cls, face):
        """ generated source for method getUAxis """
        if face==0:
            return S2Point(0, 1, 0)
        elif face==1:
            return S2Point(-1, 0, 0)
        elif face==2:
            return S2Point(-1, 0, 0)
        elif face==3:
            return S2Point(0, 0, -1)
        elif face==4:
            return S2Point(0, 0, -1)
        else:
            return S2Point(0, 1, 0)

    @classmethod
    def getVAxis(cls, face):
        """ generated source for method getVAxis """
        if face==0:
            return S2Point(0, 0, 1)
        elif face==1:
            return S2Point(0, 0, 1)
        elif face==2:
            return S2Point(0, -1, 0)
        elif face==3:
            return S2Point(0, -1, 0)
        elif face==4:
            return S2Point(1, 0, 0)
        else:
            return S2Point(1, 0, 0)


# vim: et ts=4 sw=4
