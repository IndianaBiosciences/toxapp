#!/usr/bin/perl

use Data::Dumper;
use warnings;
use strict;

my %evidence_level = (
  'IDA' => 1,
  'IPI' => 1,
  'IMP' => 1,
  'IGI' => 1,
  'IEP' => 1,
  'EXP' => 2,
  'TAS' => 3,
  'NAS' => 4,
  'IC' => 4,
  'HDA' => 5,
  'ISS' => 6,
  'ISO' => 6,
  'ISA' => 6,
  'ISM' => 6,
  'IGC' => 6,
  'IBD' => 6,
  'IKR' => 6,
  'IRD' => 6,
  'RCA' => 6,
  'IBA' => 6,
  'IEA' => 7,
);

my %rel2grade = (
   'is_a' => 1,
   'part_of' => 1,
   'positively_regulates' => 2,
   'negatively_regulates' => 2,
   'regulates' => 2,
);

my $id2entrez;

open FLE, "RAT_10116_idmapping.dat" or die;
while (<FLE>) {
   chomp;
   my ($uni, $db, $id) = split /\t/;
   next unless ($db eq 'GeneID');
   $id2entrez->{UniProtKB}->{$uni}->{$id} = 1;
}
close FLE;

my $rgd2entrez;

open FLE, "GENES_RAT.txt" or die;

while (<FLE>) {

   next if ( /^#/ );
   my @f = split /\t/;
   next if ($f[0] eq "GENE_RGD_ID");

   my $rgd = $f[0];
   my $entrez = $f[20];

   next unless ($entrez);
   # no longer necessary - in 2021 version there is no field with multiple entrez genes
   my @entrez = split /;/, $entrez;

   for my $e (@entrez) {
      $id2entrez->{RGD}->{$rgd}->{$e} = 1;
   }
}
close FLE;

# get annotation lists for all genes in rat
# count genes annotated by each term after filling in parents

my ($id_conversion, $parents_of, $info);
print STDERR "Failed to parse ontology\n" unless (parseObo("go-basic.obo"));

# I can't quite get my head around annotating the path from a given gene to a given GO in ontology with whether it uses only is_a, part_of, or whether
# it uses the various regulates terms.  To be safe change the regex part_of|regulates|positively_regulates|negatively_regulates below
# in comparing both runs with / without regulate terms on jan 2014 files, you get ~20K terms that come out as 'is_a, part_of' when commenting out regulates
# from regex that still get annoated as using regulates from script as-is; I think my logic in the do loop at end isn't quite right;
# problem is not as simple as evidence via regulates path being stronger than via is_a, part_of; most of hte 20k pairs have same evidence level

print "entrez_gene_id\tGO_id\tevidence\tdirect_or_inferred_from_ontology\tpmid\tGO_name\tGO_type\trelationship_level(1=is_a,part_of;2=regulates)\n";

my $go_by_gene;

my $mapping_stats;
my %warned_map;
my %warned_evidence;

open FLE, "rgd.gaf" or die;
while (<FLE>){

    chomp;
    next if ( /^\!/ || /^DB/);
    my @line = split "\t";

    next if ($line[3] =~ /not/i);

    my $db = $line[0];
    die "Unsupported DB entry $db" unless ($db eq 'RGD' || $db eq 'UniProtKB');

    my $evidence = $line[6];
    my $go = $line[4];
    my $id = $line[1];
    (my $pmid) = ($line[5] =~ /PMID:(\d+)/);
    $pmid = "" unless ($pmid);

    next unless ($id && $go && $evidence);
    next if ($evidence eq 'ND'); # ND means no evidence linking a gene to BP, MF, or CC

    my @egs;

    if ($id2entrez->{$db} && $id2entrez->{$db}->{$id}) {
      @egs = keys %{$id2entrez->{$db}->{$id}};
    } else {
      $mapping_stats->{$db}->{failure}->{$id} = 1;
    }

    unless (@egs) {
      #print STDERR "Failed to map identifier $id for db $db\n" unless ($warned_map{"$db:$id"});
      $warned_map{"$db:$id"} = 1;
      next;
    }

    #next unless ($go eq 'GO:0005783');

    # switch to the standard GO ID if an alt ID is used
    # update 2015 - not using this conversion - not sure why they populate them
    if (0 && $id_conversion->{$go}) {

        my @new_ids = keys %{$id_conversion->{$go}};
        if (scalar(@new_ids) > 1) {
           print STDERR "have multiple converted Ids for go term $go; taking first only\n";
        }
        my $new_id = $new_ids[0];

        $go = $new_id;
    }

    $go_by_gene->{$_}->{$go} = {evidence => $evidence, source => "direct", pmid=>$pmid} for (@egs);

}

my %warned_go;

# expand out to parent terms
for my $gene ( sort keys %$go_by_gene ){

    foreach my $go ( keys %{$go_by_gene->{ $gene }} ) {

        next unless ($parents_of->{$go});
        my $evidence = $go_by_gene->{$gene}->{$go}->{evidence};
        if (!$evidence_level{$evidence}) {
            if (!$warned_evidence{$evidence}) {
                print STDERR "Evidence level not available for $evidence; skipping\n";
                $warned_evidence{$evidence} = 1;
            }
            next;
        }

        my $pmid = ($go_by_gene->{$gene}->{$go}->{pmid}) ?  $go_by_gene->{$gene}->{$go}->{pmid} : "";

        foreach my $parent (keys %{$parents_of->{$go}}) {
            # in defining parent hiearchy don't replace higher quality evidence; low values better
            next if ($go_by_gene->{$gene}->{$parent} && $evidence_level{$go_by_gene->{$gene}->{$parent}->{evidence}} < $evidence_level{$evidence} );
            # don't replace a link with a pmid id defined
            next if (!$pmid && $go_by_gene->{$gene}->{$parent} && $go_by_gene->{$gene}->{$parent}->{pmid});
            # don't replace inferred via ontology vs. direct annotation; not sure should this happen anyway
            next if ($go_by_gene->{$gene}->{$parent} && $go_by_gene->{$gene}->{$parent}->{source} eq 'direct');
            # don't use a path via the 'regulates' and related relatinoship when it exists via is_a and part_of;
            next if ($go_by_gene->{$gene}->{$parent}->{relation} && $go_by_gene->{$gene}->{$parent}->{relation} < $parents_of->{$go}->{$parent} );

            $go_by_gene->{$gene}->{$parent} = {evidence => $evidence, source => 'ontology', pmid=>$pmid, relation=>$parents_of->{$go}->{$parent}};
        }
    }

    foreach my $go ( keys %{$go_by_gene->{ $gene }} ) {

        my $name = "";
        my $type = "";
        my $relation = ($go_by_gene->{$gene}->{$go}->{relation}) ? $go_by_gene->{$gene}->{$go}->{relation} : "";

        if ($info->{$go}) {
            $name = $info->{$go}->{name};
            $type = $info->{$go}->{type};
        } else {
            print STDERR "No information on GO term $go; not printing\n" unless ($warned_go{$go});
            $warned_go{$go} = 1;
            next;
        }

        print "$gene\t$go\t$go_by_gene->{$gene}->{$go}->{evidence}\t$go_by_gene->{$gene}->{$go}->{source}\t$go_by_gene->{$gene}->{$go}->{pmid}\t$name\t$type\t$relation\n";
      }
}
print STDERR ("Mapping stats" . Dumper($mapping_stats));


sub parseObo {

   my $file = shift;

   open OBO, $file or die;

   my $read = 0;

   my $go;
   my %parents;

   while (<OBO>) {

       chomp;
       $read = 1 if ( /^\[Term\]/ );
       $read = 0 unless ( /\w/ );

       if ( $read == 0 ){
           # store everything up into hash

         for my $p ( keys %parents ){
            $parents_of->{$go}->{$p} = $parents{$p};
         }

           # clear variable values
           undef $go;
           undef %parents;
       }

       if ( $read == 1 ){
           # store pertinent information line by line
         if ( /^id\: (GO\:\d{7})/ ){ # id
               $go = $1;
         } elsif ( /^name: (.+)$/) {
            $info->{$go}->{name} = $1;
         } elsif ( /^namespace: (.+)$/) {
            $info->{$go}->{type} = $1;
         } elsif ( /^alt_id\: (GO\:\d{7})/ ) {
            $id_conversion->{$go}->{$1} = 1;
            #$log->debug("Captured id conversion from $go to $1");
         } elsif ( /^is_a: (GO\:\d{7})/) {
            $parents{$1} = $rel2grade{'is_a'};
            #$log->debug("Captured $1 of type is_a");
         } elsif ( /^relationship\: (part_of|regulates|positively_regulates|negatively_regulates) (GO\:\d{7})/) {
         #} elsif ( /^relationship\: (part_of) (GO\:\d{7})/) {
            $parents{$2} = $rel2grade{$1};
            #$log->debug("Captured parent $2 of type $1");
           }
       }
   }

   my $new = 0;

   do {
       $new = 0;
       # loop through hash, add parents of parents and count newly added
       foreach my $go (keys %{$parents_of}) {
           foreach my $parent (keys %{$parents_of->{$go}}) {
               my $type_parent = $parents_of->{$go}->{$parent};
               foreach my $gparent (keys %{$parents_of->{$parent}}){

               my $type_gparent = $parents_of->{$parent}->{$gparent};

               # capture the weakest link from child to parent, in terms of relationship strength - is_a, part_of, etc.
               my $weak_link = ($type_gparent > $type_parent) ? $type_gparent : $type_parent;
               if (!$parents_of->{$go}->{$gparent} || $parents_of->{$go}->{$gparent} > $weak_link) {
                  $parents_of->{$go}->{$gparent} = $weak_link;
                       $new++;
                   }
               }
           }
       }
   } until ( $new == 0 );

   1;

}
