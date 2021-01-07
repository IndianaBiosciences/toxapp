#!/usr/bin/perl

use warnings;
use strict;
use Data::Dumper;
use XML::Twig;

my $file = shift;

unless ($file && -r $file) {
   print STDERR "No readable MSigDB XML file\n";
   exit(1);
}

my %orthologs;
open(FLO, "RGD_ORTHOLOGS.txt") or die "Cannot read RGD_orthologs.txt";
while (<FLO>) {
    chomp;
    next if ( /^#/ );
    my @f = split /\t/;
    next if ($f[0] eq "RAT_GENE_SYMBOL");
    my $rat_eg = $f[2];
    my $human_egs_txt = $f[5];
    next unless ($rat_eg && $human_egs_txt);
    my @human_egs = split /\|/, $human_egs_txt;
    # on Jan 2021, there are only 3 genes with '|' - i.e. multiple human genes
    # for a rat gene.  And they are all the same e.g. 1234|1234

    for my $human_eg ( @human_egs ) {
         $orthologs{$human_eg} = $rat_eg;
    }
}

print STDERR "Number of rat orthologs from RGD: " . scalar(keys %orthologs) . "\n";

my %valid_genes;
open(FLG, "gene_info") or die "Cannot read gene_info for validating against current entrez";
my $head = <FLG>;
while (<FLG>) {
    my ($taxon, $geneid, $symbol) = split /\t/;
    next if ($taxon != 9606);
    $valid_genes{$geneid} = $symbol
}
close FLG;

print STDERR "Number of valid human genes from entrez: " . scalar(keys %valid_genes) . "\n";

my %history;
open(FLH, "gene_history") or die "Cannot read gene_history for validating against current entrez";
$head = <FLH>;
while (<FLH>) {
    my ($taxon, $current_geneid, $old_geneid) = split /\t/;
    next if ($taxon != 9606);
    next if ($current_geneid eq '-');
    $history{$old_geneid} = $current_geneid
}
close FLH;

print STDERR "Number of history genes with current valid gene from entrez: " . scalar(keys %history) . "\n";

my @wantedCols = (
   'CATEGORY_CODE',
   'SUB_CATEGORY_CODE',
   'STANDARD_NAME',
   'SYSTEMATIC_NAME',
   'ORGANISM',
   'PMID',
   'EXTERNAL_DETAILS_URL',
   'CONTRIBUTOR',
   'CONTRIBUTOR_ORG',
   'DESCRIPTION_BRIEF'
);

my %cat_description = (
   'C2' => 'curated gene sets',
   'C3' => 'motif gene sets',
   'C6' => 'oncogenic sigs (C6)',
   'C7' => 'immunologic sigs (C7)',
   'C8' => 'cell type sigs (C8)',
   'H' => 'cancer hallmark sigs (H)'
);

my %invalid_genes;
my %remapped_genes;
my %no_ortholog_genes;

my $sigs;

my $twig = XML::Twig->new( twig_handlers=>{GENESET => \&parseGeneSet } );
$twig->parsefile($file);

open(my $sig_desc, ">MSigDB_descriptions.txt") or die;
open(my $sig_genes, ">MSigDB_genes.txt") or die;

print $sig_desc join("\t", 'CATEGORY_DESCRIPTION', @wantedCols) . "\n";
print $sig_genes "sig_name\tentrez_gene\tgene_symbol\trat_entrez_gene\tsub_category\tdescription\n";

for my $sig (sort {$sigs->{$a}->{CATEGORY_CODE} cmp $sigs->{$b}->{CATEGORY_CODE} || $sigs->{$a}->{SUB_CATEGORY_CODE} cmp $sigs->{$b}->{SUB_CATEGORY_CODE}} keys %{$sigs}) {

   next if ($sigs->{$sig}->{CATEGORY_CODE} eq 'ARCHIVED');

   my $cat_desc = $cat_description{$sigs->{$sig}->{CATEGORY_CODE}};
   next if not $cat_desc;

   # C6, C7, C8 and H do not have subcategory; since the CATEGORY was not used in earlier builds of CTox MSigDB sigs
   # put something in this field here
   $sigs->{$sig}->{SUB_CATEGORY_CODE} = $cat_desc if not $sigs->{$sig}->{SUB_CATEGORY_CODE};

   # skip gene sets with <3 or >5000 GENESET
   my $num_genes = scalar(@{$sigs->{$sig}->{egs}});
   if ($num_genes < 3 || $num_genes > 5000) {
      print STDERR "Skipping geneset $sigs->{$sig}->{STANDARD_NAME}\n";
      next;
   }

   print $sig_desc $cat_desc;
   for my $col (@wantedCols) {
      my $val = defined ($sigs->{$sig}->{$col}) ? $sigs->{$sig}->{$col} : "";
      print $sig_desc "\t$val";
   }

   print $sig_desc "\n";

   for my $gene (@{$sigs->{$sig}->{egs}}) {

      my $valid_eg = undef;
      if ($valid_genes{$gene}) {
          $valid_eg = $gene;
      } elsif ($history{$gene}) {
          $valid_eg = $history{$gene};
          $remapped_genes{$gene} = 1;
      } else {
          $invalid_genes{$gene} = 1;
          next;
      }

      my $human_gs = $valid_genes{$valid_eg};
      my $rat_eg = $orthologs{$valid_eg};
      next unless ($rat_eg);

      print $sig_genes "$sig\t$valid_eg\t$human_gs\t$rat_eg\t$sigs->{$sig}->{SUB_CATEGORY_CODE}\t$sigs->{$sig}->{DESCRIPTION_BRIEF}\n";
   }
}

print STDERR "Discarded " . scalar(keys %invalid_genes). " genes without valid entrez info\n";
print STDERR "Remapped " . scalar(keys %remapped_genes). " to current valid EGs\n";


sub parseGeneSet {

   my ($twig, $rec) = @_;

   my %data;

   my $name = $rec->{'att'}->{'STANDARD_NAME'};
   unless ($name) {
      print STDERR "Failed to extract signature name from record; something wrong\n";
      return;
   }

   for my $c (@wantedCols) {
      my $val = $rec->{'att'}->{$c};
      $data{$c} = $val;
   }

   my $eg_str = $rec->{'att'}->{'MEMBERS_EZID'};
   unless ($eg_str) {
      print STDERR "Faild to get genes from record $name; skipping\n";
      return;
   }

   my @egs = split /,/, $eg_str;

   $sigs->{$name} = \%data;
   $sigs->{$name}->{egs} = \@egs;
}
