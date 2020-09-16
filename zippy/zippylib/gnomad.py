import subprocess, argparse, sys, re, os, logging, pysam, shutil, gzip
logger = logging.getLogger(__name__)


class GnomadChromosomeInfo:
    def __init__(self, gnomad_version, info_type, chromosome_id):
        self.gnomad_version = gnomad_version
        self.info_type = info_type
        self.chromosome_id = chromosome_id
        self.vcf_found = False
        self.tbi_found = False

    @staticmethod
    def gather_file(gs_folder, file_basename, dest_folder):
        filefullpath = os.path.join(dest_folder, file_basename)
        if os.path.exists(filefullpath):
            pass  # TODO make a checksum
        else:
            file_uri = os.path.join(gs_folder, file_basename)
            logger.info(f"Getting file {file_uri}")
            dest_folder_norm = os.path.normpath(dest_folder)
            rsync_cmd = f"gsutil cp {file_uri} {dest_folder_norm}/"
            sp = subprocess.Popen(rsync_cmd, shell=True)
            statuscode = sp.wait()
            if statuscode > 0:
                raise Exception("The last gsutil command raised a non-zero status " +
                                f"code of {statuscode}.")

    def gather_data(self, resources_folder):
        from . import files  # import until here to avoid circular importing
        assert self.vcf_found and self.tbi_found
        file_basename = f"gnomad.{self.info_type}.r{self.gnomad_version}.sites." + \
            f"{self.chromosome_id}.vcf.bgz"
        stripped_file_basename = f"gnomad.{self.info_type}.r{self.gnomad_version}.sites." + \
            f"{self.chromosome_id}.stripped.vcf.bgz"
        self.index_file_txt_fullpath = os.path.join(resources_folder, file_basename + ".tbi")
        self.file_fullpath = os.path.join(resources_folder, file_basename)
        self.index_file_fullpath = os.path.join(resources_folder, file_basename + ".tbi")
        self.stripped_index_file_txt_fullpath = os.path.join(resources_folder,
                                                             stripped_file_basename + ".tbi")
        self.stripped_file_fullpath = os.path.join(resources_folder, stripped_file_basename)
        self.stripped_file_fullpath_text = os.path.join(resources_folder,
                                                        f"gnomad.{self.info_type}.r{self.gnomad_version}.sites.{self.chromosome_id}.stripped.vcf")
        if os.path.exists(self.stripped_file_fullpath):
            logger.info(f"File {self.stripped_file_fullpath} already found")
        else:
            gs_folder = f"gs://gnomad-public/release/{self.gnomad_version}/vcf/{self.info_type}"
            vcf_file = f"{file_basename}"
            tbi_file = f"{file_basename}.tbi"
            self.gather_file(gs_folder, vcf_file, resources_folder)
            self.gather_file(gs_folder, tbi_file, resources_folder)
            #files.VCF.create_stripped_vcf(self.file_fullpath,
            #                              self.stripped_file_fullpath)
        #self.compress_data(resources_folder, deambiguate=False)
        #self.test_compressed_data(resources_folder)

    def test_compressed_data(self, resources_folder):
        assert 0, self.stripped_file_fullpath_text
        #with pysam.VariantFile(self.stripped_file_fullpath_text, "r", index_filename=self.index_file_txt_fullpath) as invcffileobj:
        with pysam.VariantFile(self.stripped_file_fullpath_text, "r") as invcffileobj:
        #with pysam.VariantFile(self.stripped_file_fullpath, "rb", index_filename=self.index_file_txt_fullpath) as invcffileobj:
        #with pysam.VariantFile(self.stripped_file_fullpath, "rb") as invcffileobj:
            for record in invcffileobj:
                print("record", record)
        #with pysam.TabixFile(self.stripped_file_fullpath, "r", index=self.stripped_index_file_txt_fullpath) as invcffileobj:
        #    for record in invcffileobj.fetch():
        #        print("record", record)
        #        break

    def compress_data(self, resources_folder, deambiguate=False):
        if deambiguate:
            shutil.move(self.stripped_file_fullpath, self.stripped_file_fullpath_txt)
        shutil.copy2(self.stripped_file_fullpath, self.stripped_file_fullpath_text)
        with gzip.open(self.stripped_file_fullpath, "wb") as gzipout, open(self.stripped_file_fullpath_text, "rb") as gzipin:
            shutil.copyfileobj(gzipin, gzipout)
        #shutil.copy2(self.index_file_txt_fullpath, self.stripped_index_file_txt_fullpath)
        if False:
            #with pysam.VariantFile(self.stripped_file_fullpath_text, "r") as invcffileobj:
            with pysam.VariantFile(self.stripped_file_fullpath, "r") as invcffileobj:
                for record in invcffileobj.fetch():
                    assert 0, str(record)
            #with pysam.VariantFile(self.stripped_file_fullpath, "wb") as outvcffileobj, \
            #   pysam.VariantFile(self.stripped_file_fullpath_text, "r") as invcffileobj:
            #    for record in invcffileobj.fetch():
            #        outvcffileobj.write(record)


def get_files(gnomad_version, info_type, resources_folder):
    chromosomes_infos = {}
    #gs_folder = f"gs://gnomad-public/release/{gnomad_version}/vcf/{info_type}"
    #sp = subprocess.Popen(f"gsutil ls {gs_folder}", shell=True,
    #    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #statuscode = sp.wait()
    #errors = list(sp.stderr)
    #files = list(sp.stdout)
    #filepartsre = re.compile(f"{gs_folder}/gnomad.{info_type}.r{gnomad_version}.sites.(.*).vcf.bgz(.tbi)?")
    nums = list(range(1, 23))
    nums.append("X")
    if False:
        for file in files:
            file = file.strip().decode("UTF-8")
            match = filepartsre.match(file)
            if match:
                mg = match.groups()
                if mg[0] not in chromosomes_infos:
                    chromosomes_infos[mg[0]] = GnomadChromosomeInfo(gnomad_version, info_type, mg[0])
                if mg[1] is None:
                    chromosomes_infos[mg[0]].vcf_found = True
                else:
                    chromosomes_infos[mg[0]].tbi_found = True
    for num in nums:
        numstr = str(num)
        chromosomes_infos[numstr] = GnomadChromosomeInfo(gnomad_version, info_type, numstr)
        chromosomes_infos[numstr].vcf_found = True
        chromosomes_infos[numstr].tbi_found = True
    for (chromid, chromobj) in chromosomes_infos.items():
        chromobj.gather_data(resources_folder)
    return chromosomes_infos


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", default="2.1.1")
    parser.add_argument("-r", "--resources_folder", default="/var/local/zippy/resources")
    args = parser.parse_args()
    get_files(args.version, "genomes", args.resources_folder)
