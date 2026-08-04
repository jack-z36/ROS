std_msgs/Header header      # stamp used for permit freshness / expiry checks
bool allowed                # true = human permit valid, new commands may execute
string reason_code          # empty when allowed=true; stable non-empty code when allowed=false
