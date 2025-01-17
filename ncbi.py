import Bio.Phylo as bp
from Bio.Phylo import BaseTree
from Bio.Phylo.PhyloXML import Clade
from Bio.Phylo.PhyloXML import Taxonomy as tx
import os
import tarfile
from collections import defaultdict
from taxonomy import Taxonomy
from Bio.Phylo import PhyloXMLIO
from Bio.Phylo.PhyloXML import Phylogeny 



class Ncbi(Taxonomy):
    name = 'ncbi'
    
    def main(self, tree_filename, tree_format='newick', ids=None):
        col_delimiter = '\t|\t'
        row_delimiter = '\t|\n'
        url = 'ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz'
        
        # download the taxonomy archive
        filename = self.download_file(url)
        
        # extract the text dump
        for extract in ('nodes.dmp', 'names.dmp'):
            if os.path.exists(os.path.join(self.data_dir, extract)):
                print('Using existing copy of %s' % extract)
            else:
                print('Extracting %s from %s...' % (extract, filename))
                archive = tarfile.open(name=filename, mode='r:gz')
                archive.extract(extract, path=self.data_dir)
                archive.close()
        
        # get names for all tax_ids from names.dmp
        print ('Getting names...')
        scientific_names = {}
        other_names = defaultdict(set)
        name_types = set()
        with open(os.path.join(self.data_dir, 'names.dmp')) as names_file:
            for line in names_file:
                line = line.rstrip(row_delimiter)
                values = line.split(col_delimiter)
                tax_id, name_txt, _, name_type = values[:4]
                name_types.add(name_type)
                if name_type == 'scientific name':
                    scientific_names[tax_id] = name_txt
                else:
                    other_names[tax_id].add(name_txt)

        print(name_types)
        # read all node info from nodes.dmp
        print ('Reading taxonomy...')
        nodes = {}
        with open(os.path.join(self.data_dir, 'nodes.dmp')) as nodes_file:
            for line in nodes_file:
                line = line.rstrip(row_delimiter)
                values = line.split(col_delimiter)
                tax_id, parent_id = values[:2]
                if ids:
                    this_node = Clade(name=tax_id)
                else:
                    this_node = Clade(name=scientific_names[tax_id])
                
                nodes[tax_id] = this_node
                this_node.parent_id = parent_id

                if tree_format == 'phyloxml':
                    # add common names, synonyms, mispellings, etc.
                    if len(other_names[tax_id]) > 0:
                        this_node.taxonomies = [tx(synonyms=list(other_names[tax_id]))]


        
        print ('Found %s OTUs.' % len(nodes))
        
        # create tree from nodes dictionary
        print ('Building tree...')
        for node_id, this_node in nodes.items():
            if node_id == this_node.parent_id:
                root_node = this_node
                print ('Found root.')
            else:
                parent_node = nodes[this_node.parent_id]
                parent_node.clades.append(this_node)
                
            del this_node.parent_id
        
        #tree = BaseTree.Tree(root=root_node)
        tree = Phylogeny(root=root_node)
        
        # write tree to file
        print ('Writing %s tree to %s...' % (tree_format, tree_filename))

        bp.write([tree], tree_filename, tree_format)
        
        print ('Done!')
