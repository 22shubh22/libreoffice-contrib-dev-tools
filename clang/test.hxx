class A
{
};

class C
{
public:
    int nX, nY, nZ;
    int* pX;
    static const int aS[];
    // This is intentionally not initialized explicitly in C::C().
    A aA;
    union {
        int nFoo;
        int nBar;
    } aUnion;
    C();
    ~C();

    static const int* getS() { return aS; }
};

namespace ns
{
class C
{
public:
    int nX, mnY, m_nZ;

    C() { }
};
/// This has no ctor/dtor/member functions, so members are OK to be not prefixed.
struct S
{
    int nX, mnY, m_nZ;
};
}

#define DELETEZ( p )    ( delete p,p = 0 )

void sal_detail_logFormat(char const * /*area*/, char const * /*where*/, char const * /*format*/, ...) { }
#define SAL_DETAIL_LOG_FORMAT(condition, area, ...) \
    do { \
        if (condition) { \
            sal_detail_logFormat((area), __VA_ARGS__); \
        } \
    } while (0)
#define SAL_DETAIL_WARN_IF_FORMAT(condition, area, ...) \
    SAL_DETAIL_LOG_FORMAT( \
        (condition), \
        area, __VA_ARGS__)
#define OSL_ENSURE(c, m) SAL_DETAIL_WARN_IF_FORMAT(!(c), "legacy.osl", "%s", m)

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
