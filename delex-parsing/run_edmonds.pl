#!/usr/bin/env perl

use utf8;
use open ':utf8';
use List::MoreUtils qw(uniq);


use Graph;
use Graph::Directed;
use Graph::ChuLiuEdmonds;

binmode(STDIN, ':utf8');
binmode(STDOUT, ':utf8');
binmode(STDERR, ':utf8');


while (<>)
{
	my @fields = split / /,$_;
	my $n = scalar @fields;
	# print($n."\n");
	my @temp = ();
	my $idx = 0;
	for (my $i=0; $i<$n; ++$i)
	{
		if ( ($i+1) % 3 == 0 )	{next;}
		$temp[$idx] = $fields[$i];
		$idx++;
	}
	my @vertices = uniq @temp;
	
	# print join(",",@vertices);
	# print("\n");

	my $graph = Graph::Directed->new(vertices=>[@vertices]);
	$graph->add_weighted_edges(@fields);
	my $msts = $graph->MST_ChuLiuEdmonds($graph);

	print($msts);
}