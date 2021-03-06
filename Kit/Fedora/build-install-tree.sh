#!/usr/bin/bash
set -e

echo "Info: build-install-tree.sh"
# BUILD_ROOT is the build prefix e.g. /var/mock/xxx
BUILD_ROOT=${1:? build root}
# BIN, LIB, MAN1 and DESKTOPFILES are path on the target e.g. /usr/bin etc
BIN=${2? bin folder}
LIB=${3? lib folder}
MAN1=${4? man1 folder}
DESKTOPFILES=${5? desktop files folder}

mkdir -p ${BUILD_ROOT}${BIN} ${BUILD_ROOT}${LIB} ${BUILD_ROOT}${MAN1} ${BUILD_ROOT}${DESKTOPFILES}

gzip -c ${BUILDER_TOP_DIR}/Kit/Fedora/scm-workbench.1 > ${BUILD_ROOT}${MAN1}/scm-workbench.1.gz
cp ${BUILDER_TOP_DIR}/Kit/Fedora/scm-workbench.desktop ${BUILD_ROOT}${DESKTOPFILES}

PROG=${BUILD_ROOT}${BIN}/scm-workbench
cat <<EOF >${PROG}
#!/usr/bin/python3
import sys
sys.path.insert( 0, "${LIB}" )
EOF
cat ${BUILDER_TOP_DIR}/Source/Scm/wb_scm_main.py >>${PROG}
chmod +x ${PROG}
unset PROG

PROG=${BUILD_ROOT}${BIN}/scm-workbench-askpass
echo '#!/usr/bin/python3' >${PROG}
cat ${BUILDER_TOP_DIR}/Source/Git/wb_git_askpass_client_unix.py >>${PROG}
chmod +x ${PROG}
unset PROG

pushd ${BUILDER_TOP_DIR}/Source/Scm
make -f linux.mak
popd
pushd ${BUILDER_TOP_DIR}/Source/Common
make -f linux.mak
popd

for LIBSRC in \
    ${BUILDER_TOP_DIR}/Source/Common \
    ${BUILDER_TOP_DIR}/Source/Git \
    ${BUILDER_TOP_DIR}/Source/Hg \
    ${BUILDER_TOP_DIR}/Source/Svn \
    ${BUILDER_TOP_DIR}/Source/Scm
do
    cp ${LIBSRC}/*.py ${BUILD_ROOT}${LIB}
done

cp ${BUILDER_TOP_DIR}/Source/wb.png ${BUILD_ROOT}${LIB}/scm-workbench.png
