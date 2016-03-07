"""The protein module"""

import cStringIO

from cached_property import cached_property
from Bio import SeqIO

import entrez_utils


class Protein:
    """Definition for Protein class.

    Protein class contains attributes and methods to represent a protein. The
    constructor queries the given accession number and fetches the record from
    NCBI Protein database. The class provides methods to access the protein
    features such as its description and amino acid sequence.
    """

    def __init__(self, accession_number, name):
        self._name = name
        self._record = entrez_utils.get_protein_record(accession_number)

    @cached_property
    def record(self):
        """Returns the Biopython SeqRecord created from the NCBI record."""
        return SeqIO.read(cStringIO.StringIO(self._record), 'gb')

    @property
    def accession_number(self):
        """Returns the accession number of the protein."""
        return self.record.id

    @property
    def name(self):
        """Returns the name of the protein."""
        return self._name

    @property
    def description(self):
        """Returns the description of the protein."""
        return self.record.description

    @property
    def sequence(self):
        """Returns the amino acid sequence of the protein."""
        return str(self.record.seq)

    def to_fasta(self):
        """Returns the protein record as a string in FASTA format."""
        output = cStringIO.StringIO()
        SeqIO.write(self.record, output, 'fasta')
        return output.getvalue()

    def __repr__(self):
        return self.accession_number + ': ' + self.description
