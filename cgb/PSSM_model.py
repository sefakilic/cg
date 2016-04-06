from cached_property import cached_property
from Bio.Seq import Seq
from Bio.motifs.matrix import PositionWeightMatrix


from binding_model import TFBindingModel
from misc import log2


class PSSMModel(TFBindingModel):
    """Class definition for PSSM model for TF-binding analysis.

    PSSMModel class based on the ubiquitous PSSM model for TF-binding
    analysis. The PSSM method assumes positional independence in the TF-binding
    motif and computes a sum-of-log-likehood ratios as a reasonable
    approximation to the TF-binding energy contribution of any given
    sequence. The likelihood ratio is based on a position-independent
    probability model (the PSWM) and a background model. To make the model
    generic, a uniform background is assumed by default.

    The PSSMModel subclass incorporates a constructor based on the
    weighted mixing of collections of PSWMs that allows instantiating
    species-specific PSSM models based on available evidence in different
    species and a phylogenetic model of these species relationship with the
    target species.
    """
    def __init__(self, collections, weights,
                 background={'A': 0.25, 'C': 0.25, 'G': 0.25, 'T': 0.25}):
        """Constructor for the PSSMModel class."""
        super(PSSMModel, self).__init__(collections, background)
        self._pwm = self._combine_pwms([c.pwm for c in collections], weights)

    @cached_property
    def pwm(self):
        """Returns the position-weight-matrix."""
        return self._pwm

    @cached_property
    def length(self):
        """Returns the length of the combined PWM."""
        return self.pwm.length

    @cached_property
    def pssm(self):
        """Returns the position-specific scoring matrix."""
        return self._pwm.log_odds(self.background)

    @cached_property
    def reverse_complement_pssm(self):
        """Returns the reverse complement of the PSSM."""
        return self.pssm.reverse_complement()

    @property
    def alphabet(self):
        """Returns the alphabet of the motif."""
        return self.pwm.alphabet

    @cached_property
    def IC(self):
        """Returns the information content of the PSSM."""
        return self.pssm.mean()

    @cached_property
    def patser_threshold(self):
        """Returns the threshold as used in Hertz, Stormo 1999.

        Patser-threshold satisfies the equality between the -log of the
        false-positive-rate and the information-content -- -log(FPR) = IC
        """
        dist = self.pssm.distribution(precision=10**3)
        return dist.threshold_patser()

    def threshold(self, threshold_type='patser'):
        if threshold_type == 'patser':
            thr = self.patser_threshold
        else:
            raise ValueError
        return thr

    @cached_property
    def sites(self):
        """Returns the binding sites of the motifs used to build the model."""
        return [site for coll in self._collection_set for site in coll.sites]

    def score_self(self):
        """Returns the list of scores of the sites that the model has."""
        return [self.score_seq(site) for site in self.sites]

    def score_seq(self, seq, both=True):
        """Returns the PSSM score for a given sequence for all positions.

        The scores from both strands are combined with the soft-max function.

        Args:
            seq (string): the sequence to be scored
        Returns:
            [float]: list of scores of all positions.
        """
        seq = Seq(seq, self.alphabet)
        scores = self.pssm.calculate(seq)
        rc_scores = self.reverse_complement_pssm.calculate(seq)

        if self.length == len(seq):
            # Biopython returns single number if len(seq)==len(pssm)
            scores, rc_scores = [scores], [rc_scores]

        if both:
            scores = [log2(2**score + 2**rc_score)
                      for score, rc_score in zip(scores, rc_scores)]
        return scores

    @staticmethod
    def _combine_pwms(pwms, weights):
        """Combines the given PWMs according to the given weights."""
        len = pwms[0].length
        alphabet = pwms[0].alphabet
        # Check if all PWMs are of the same length.
        assert all(len == pwm.length for pwm in pwms)
        # Check if all PWMs have the same alphabet -- 'ACGT'
        assert all(alphabet == pwm.alphabet for pwm in pwms)
        # Normalize weights
        weights = [float(weight)/sum(weights) for weight in weights]
        # Combine all PWMs according to given weights
        pwm_vals = {let: [sum(pwm[let][i]*w for pwm, w in zip(pwms, weights))
                          for i in xrange(len)]
                    for let in alphabet.letters}
        return PositionWeightMatrix(alphabet, pwm_vals)