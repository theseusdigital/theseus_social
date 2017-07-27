. /home/nishant/theseus_social/shscripts/common.sh
echo "socialmediafacebook 30 days"
$PY_EXEC tracker/socialmediafacebook.py 30

echo "socialmediatwitter 30 days"
$PY_EXEC tracker/socialmediatwitter.py 30

echo "socialmediayoutube 30 days"
$PY_EXEC tracker/socialmediayoutube.py 30

deactivate