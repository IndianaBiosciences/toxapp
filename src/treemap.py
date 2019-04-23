from tp.models import GeneSets, GSAScores, Experiment
from django.conf import settings

import logging
import os
import csv
import collections
import configparser
import pickle
import copy
import numpy as np
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class TreeMap:

    def __init__(self, testmode=False):

        self.genesets = collections.defaultdict(dict)
        self._edges = dict()
        self._height = dict()
        self._child2parent = dict()
        self._parent2child = collections.defaultdict(list)
        self.nodes = dict()

        config_file = os.path.join(settings.BASE_DIR, 'data/toxapp.cfg')
        if not os.path.isfile(config_file):
            raise FileNotFoundError('Configuration file {} not readable'.format(config_file))

        config = configparser.ConfigParser()
        config.read(config_file)

        # restore from a stored version
        if not testmode:
            logger.debug('Initializing tree from pickled file')
            with open(os.path.join(settings.BASE_DIR, config['DEFAULT']['pathway_treemap']), 'rb') as fp:
                self.nodes = pickle.load(fp)
        # setup from R output
        else:
            self.parse_files()

    def parse_files(self):
        """
        Action:  read the files to generate nodes
        Returns: Nodes

        """
        config_file = os.path.join(settings.BASE_DIR, 'data/toxapp.cfg')
        if not os.path.isfile(config_file):
            raise FileNotFoundError('Configuration file {} not readable'.format(config_file))

        config = configparser.ConfigParser()
        config.read(config_file)

        files = [
            [1, 'dendrogram', None],
            [2, 'labels', None],
            [3, 'edges', None],
            [4, 'heights', None]
        ]

        for f in files:
            file_short = config['DEFAULT']['pathway_treemap_prefix'] + '_' + f[1] + '.txt'
            file_long = os.path.join(settings.BASE_DIR, config['DEFAULT']['pathway_treemap_files'], file_short)
            if os.path.isfile(file_long):
                f[2] = file_long
            else:
                raise FileNotFoundError('File {} not located'.format(file_long))

        # the R input file contained geneset names; note that the IDs in first column are just the column sequence
        # in R, and not the database ID for this geneset; geneset IDs need to be retrieved
        labels_file = files[1][2]
        logger.debug('Reading the labels file %s', labels_file)
        with open(labels_file) as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # drop header
            for row in reader:
                r_id = int(row[0])
                name = row[1]
                self.genesets[r_id]['name'] = name
                try:
                    geneset_obj = GeneSets.objects.get(name__iexact=name)
                except GeneSets.DoesNotExist:
                    raise Exception('Geneset of name {} from R output does not exist in database'.format(name))

                self.genesets[r_id]['database_id'] = geneset_obj.id
                self.genesets[r_id]['size'] = geneset_obj.members.count()
                self.genesets[r_id]['desc'] = geneset_obj.desc

        edge_file = files[2][2]
        logger.debug('Reading the edge file %s', edge_file)
        with open(edge_file) as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # drop header
            last_val = None
            for row in reader:
                # bp value in column 2 - values >= 0.95 support rejection of the edge
                edge_id = -1*int(row[0])  # terminal edge labels have negative values in dendrogram files
                sig = float(row[1])
                self._edges[edge_id] = sig
                last_val = sig

            if last_val >= 0.95:
                raise Exception('Need to manually set the significance of the very last edge (top of tree) to 0 - pvcluster quirk')

        height_file = files[3][2]
        logger.debug('Reading the height file %s', height_file)
        with open(height_file) as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                edge_id = -1*int(row[0])
                self._height[edge_id] = float(row[1])

        # read the dendrogram
        dendro_file = files[0][2]
        logger.debug('Reading the dendrogram file %s', dendro_file)
        with open(dendro_file) as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                parent = -1*int(row[0])

                # R writes out the terminal nodes with negative IDs in the dendrogram file
                child1 = -1*int(row[1])
                child2 = -1*int(row[2])
                self._child2parent[child1] = parent
                self._child2parent[child2] = parent
                self._parent2child[parent].append(child1)
                self._parent2child[parent].append(child2)

        # iterate through terminal nodes and trace up the tree to the highest non-significant edge
        for bn in self.genesets:

            attrs = self.genesets[bn]

            parent_id = self.get_first_ancestor(bn)

            # the non-terminal nodes have a leading minus sign
            label_id = parent_id if (parent_id >= 0) else -1 * parent_id

            # barcode is used throughout as a node identifier to be used in the json data received by Highcharts; not just a plain
            # id, but something that conveys info on whether something is a geneset (base node) or cluster - i.e. non-based node
            parent_barcode = 'cluster_id' + str(label_id)

            barcode = 'geneset_id_' + str(attrs['database_id'])
            node = {'id': barcode, 'name': attrs['name'], 'value': attrs['size'], 'terminal': True, 'parent': parent_barcode,
                    'height': 0, 'colorValue': None, 'desc': attrs['desc']}
            self.nodes[barcode] = node

            # iteratively add all the parents up to the top of the tree
            steps = 0
            while True:
                steps += 1
                parent_id = self.create_and_get_next(parent_id, parent_barcode)
                parent_barcode = None  # only used to set the treemap node ID for the baseclusters
                if parent_id is None:
                    logger.debug('Terminated at top of tree for base node %s with %s steps', bn, steps)
                    break

        return self.nodes

    def get_first_ancestor(self, child):
        """
        Action: Gets the first ancestor of a child node. Goes to the top of the trea from each child and determines which common ancestor each they all have that is also closest to the base of the tree.
        Returns: Returns ancestor found

        """
        nonsig_height = dict()

        # travel to the top of the tree for each child, and find a common ancestor to all children that is as close as possible to tree base
        edge_height = 0
        nonsig_edge_count = 0
        query = child
        while True:
            edge_height += 1
            this_parent = self._child2parent.get(query, None)
            if this_parent is None:  # at the top of the tree
                break

            parent_sig = self._edges[this_parent]
            if parent_sig >= 0.95:
                nonsig_height[this_parent] = edge_height
                nonsig_edge_count += 1

            query = this_parent

        if nonsig_height:
            nonsig_height_sorted = sorted(nonsig_height, key=nonsig_height.get)

            heightest_nonsig_parent = nonsig_height_sorted[-1]
            # get this node's parent
            ancestor = self._child2parent.get(heightest_nonsig_parent, None)
            logger.debug('For base node %s, number of nonsig edges: %s; height of highest non-sig edge: %s', child,
                         nonsig_edge_count, nonsig_height[heightest_nonsig_parent])

        else:
            # edges all the way up were significant
            ancestor = self._child2parent.get(child, None)
            logger.debug('For base node %s, edges were significant all the way up the tree', child)

        if ancestor is None:
            logger.error('No selected parent; not a single significant edge all the way up tree from %s ?', child)
        else:
            # update parent from the child2parent dict so that further trace-ups go right to this node
            self._child2parent[child] = ancestor

        return ancestor

    def create_and_get_next(self, this_id, this_barcode=None):
        """
        Action:  Creates a node and gets the next node.
        Returns: Parent node ID

        """
        if not this_barcode:
            # the non-terminal nodes have a leading minus sign
            label_id = this_id if (this_id >= 0) else -1 * this_id
            this_barcode = 'cluster_id' + str(label_id)

        # only create the node if seen for the first time - as we climb the tree the same parents will be encountered from
        # multiple base nodes
        if this_barcode not in self.nodes:

            parent_id = self._child2parent.get(this_id, None)
            parent_barcode = None
            # TODO - 15 is an arbitrary value for height cutoff that worked well for this dataset, perhaps not others ...
            if parent_id and self._height[parent_id] < 15:
                parent_label_id = parent_id if (parent_id >= 0) else -1 * parent_id
                parent_barcode = 'cluster_id' + str(parent_label_id)
            elif parent_id:
                logger.debug('Parent of %s was above the cut line', this_barcode)
            children_gene_count, largest_child = self.get_gene_count_and_largest_child(this_id)
            this_name = largest_child + ' and related...'
            ref = {'id': this_barcode, 'name': this_name, 'value': children_gene_count, 'terminal': False,
                   'height': self._height[this_id], 'colorValue': None}
            if parent_barcode:
                ref['parent'] = parent_barcode
            self.nodes[this_barcode] = ref

        # get and return the next parent
        parent_id = self._child2parent.get(this_id, None)
        if parent_id and self._height[parent_id] >= 15:  # truncate the tree at a height of 15
            parent_id = None

        return parent_id

    def get_gene_count_and_largest_child(self, this_id):
        """
        Action: From a given id, determines the largest child and total gene count.
        Returns: largest child and total gene count

        """
        total_gene_count = 0
        largest_child_name = None
        largest_child_gene_count = 0

        query_nodes = [this_id]

        while True:
            new_children = self.get_children(query_nodes)
            if not new_children:
                break
            else:
                query_nodes = list(set(query_nodes + new_children))

        for c in query_nodes:
            if self.genesets.get(c, None) is None:
                continue  # not a terminal node

            size = self.genesets[c]['size']
            total_gene_count += size

            if size > largest_child_gene_count:
                largest_child_gene_count = size
                largest_child_name = self.genesets[c]['name']

        return total_gene_count, largest_child_name

    def get_children(self, parents):
        """
        Action:  Given a parent, find the children of said parent node.
        Returns: Children

        """
        new_children = list()
        for p in parents:
            for c in self._parent2child[p]:
                if c in parents:
                    pass
                else:
                    new_children.append(c)

        return new_children

    def color_by_score(self, qs):
        """
        Action:  given a score value, average if multiple experiments, and return a colorValue
        Returns: Only return tree if colors are set

        """
        scoredict = collections.defaultdict(list)
        for s in qs:
            scoredict[s.geneset.name].append(s.score)

        # make a copy of the nodes attribute
        tree = copy.deepcopy(self.nodes)
        colors_set = 0
        for nid in tree:
            n = tree[nid]
            if not n['terminal']:
                continue

            scores = scoredict.get(n['name'], [])
            if not scores:
                scores = [0]

            scores = [float(s) for s in scores]
            # if multiple experiments, use the average score
            avg = sum(scores) / float(len(scores))
            n['colorValue'] = avg
            colors_set += 1

        return tree if colors_set else None

    @staticmethod
    def reduce_tree(tree):
        """
        a method to take a tree and reduce it to a single representative, most induced/repressed pathway among all
        redundant children pathways that belong to a common cluster

        The colorValue attribute must have been added using color_by_score before running this method

        The input tree is modified by the method

        :return: cluster, a dictionary keyed on the new terminal nodes which has the removed and redundant children
        nodes
        """

        # TODO - could separate the pruning process from selection of color (i.e. score) to use among redundant pathways
        # this would speed up response a little, although it works reasonably as-is; the pruning will never change, it's
        # the selection of which node to use in the cluster that will
        children = collections.defaultdict(list)
        clusters = collections.defaultdict(list)

        # don't use parent2child, child2parent which were read from R dendrogram before evaluating significance of edges
        for nid in tree:
            n = tree[nid]
            parent = n.get('parent', None)
            if parent:
                children[parent].append(n['id'])

        done = list()

        while True:

            term_nodes = list(filter(lambda x: tree[x]['terminal'] and x not in done, tree.keys()))
            if not term_nodes:
                break

            bn = tree[term_nodes[0]]
            if bn.get('colorValue', None) is None:
                raise Exception('You must use color_by_score method before calling reduce_tree')

            # does the first parent have multiple children that are all terminal nodes?
            # If so, assign them to a common cluster represented by parent
            parent = bn['parent']
            term_children = list()
            allbase = True

            for c in children[parent]:
                c_is_parent = children.get(c, None)
                if not c_is_parent:
                    term_children.append(c)
                else:
                    logger.debug('Child %s of parent %s has its own children %s', c, parent, c_is_parent)
                    allbase = False

            # sort the children by descending absolute score
            term_children_sorted = sorted(term_children, key=lambda x: abs(tree[x]['colorValue']), reverse=True)
            first = term_children_sorted[0]

            # create a label for tooltip of the most significant scoring members
            tooltxt = ''
            for c in term_children_sorted[0:5]:
                n = tree[c]
                tooltxt += n['name'] + ' (' + n['desc'][0:15] + ') score: ' + str(n['colorValue']) + '<br>'

            # if all the children are terminal nodes, drop them and keep the parent only
            if allbase:
                logger.debug('All children of parent %s are terminal nodes; all dropped', parent)
                tree[parent]['terminal'] = True
                tree[parent]['colorValue'] = tree[first]['colorValue']
                tree[parent]['toolTip'] = tooltxt
                done.append(parent)

                for c in children[parent]:
                    clusters[parent].append(c)
                    tree.pop(c)

            else:
                logger.debug('One or more chilren of parent %s are not terminal nodes; one terminal child retained',
                            parent)
                tree[first]['toolTip'] = tooltxt
                done.append(first)
                for o in term_children_sorted[1:]:
                    clusters[first].append(o)
                    tree.pop(o)

        # for non-terminal nodes, drop the colorValue
        for nid in tree:
            if not tree[nid]['terminal']:
                tree[nid].pop('colorValue')

        return clusters

    def reduce_tree_pca(self):
        """
        a method to take a tree and reduce it to a single representative, most induced/repressed pathway among all
        redundant children pathways that belong to a common cluster

        The colorValue attribute must have been added using color_by_score before running this method

        The input tree is modified by the method

        :return: cluster, a dictionary keyed on the new terminal nodes which has the removed and redundant children
        nodes
        """

        tree = copy.deepcopy(self.nodes)

        # TODO - could separate the pruning process from selection of color (i.e. score) to use among redundant pathways
        # this would speed up response a little, although it works reasonably as-is; the pruning will never change, it's
        # the selection of which node to use in the cluster that will
        children = collections.defaultdict(list)
        clusters = collections.defaultdict(list)

        exps = Experiment.objects.filter(study__source='TG')
        n_exps = exps.count()

        # don't use parent2child, child2parent which were read from R dendrogram before evaluating significance of edges
        for nid in tree:
            n = tree[nid]
            parent = n.get('parent', None)
            if parent:
                children[parent].append(n['id'])

        done = list()

        while True:

            term_nodes = list(filter(lambda x: tree[x]['terminal'] and x not in done, tree.keys()))
            if not term_nodes:
                break

            bn = tree[term_nodes[0]]

            # does the first parent have multiple children that are all terminal nodes?
            # If so, assign them to a common cluster represented by parent
            parent = bn['parent']
            term_children = list()
            allbase = True

            for c in children[parent]:
                c_is_parent = children.get(c, None)
                if not c_is_parent:
                    term_children.append(c)
                else:
                    logger.debug('Child %s of parent %s has its own children %s', c, parent, c_is_parent)
                    allbase = False

            if len(term_children) > 1:
                # sort the children by descending absolute score
                geneset_names = [tree[x]['name'] for x in term_children]
                allscores = list()

                for g in geneset_names:
                    # faster to query on a few genesets than on each experiment
                    scores = list(GSAScores.objects.filter(experiment__in=exps, geneset__name=g).order_by(
                        'experiment').values_list('score', flat=True))
                    scores = [float(s) for s in scores]
                    allscores.append(scores)

                    if len(scores) != n_exps:
                        raise Exception('Lazy loading of scores matrix improper due to missing experiment scores')

                a = np.array(allscores)
                table = np.transpose(a)
                pca = PCA(n_components=1)
                pca.fit(table)
                loadings = pca.components_[0].tolist()
                max_value = max(loadings)
                max_index = loadings.index(max_value)
                first = term_children[max_index]
                logger.debug('First PC on %s genesets explains %s fraction of variance and most highly loaded geneset is %s',
                             len(geneset_names), pca.explained_variance_ratio_, tree[first]['name'])
            else:
                # no need to do PCA if there's a single child node
                first = term_children[0]

            # if all the children are terminal nodes, drop them and keep the parent only
            if allbase:
                logger.debug('All children of parent %s are terminal nodes; all dropped', parent)
                tree[parent]['terminal'] = True
                done.append(parent)

                # the first one is the most loaded
                clusters[parent].append(first)

                for o in children[parent]:
                    tree.pop(o)
                    if o != first:  # was already added - first one
                        clusters[parent].append(o)

            else:
                logger.debug('One or more chilren of parent %s are not terminal nodes; one terminal child retained',
                            parent)
                done.append(first)

                for o in term_children:
                    if o == first:
                        continue
                    clusters[first].append(o)
                    tree.pop(o)

        return clusters
