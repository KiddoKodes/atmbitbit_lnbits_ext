/* global Vue, VueQrcode, _, Quasar, LOCALE, windowMixin, LNbits */

Vue.component(VueQrcode.name, VueQrcode)

var mapAtmBitBit = function (obj) {
  obj._data = _.clone(obj)
  return obj
}

var defaultValues = {
  name: 'My AtmBitBit',
  fiat_currency: 'EUR',
  exchange_rate_provider: 'coinbase',
  fee: '0.00'
}

new Vue({
  el: '#vue',
  mixins: [windowMixin],
  data: function () {
    return {
      checker: null,
      atmbitbits: [],
      atmbitbitsTable: {
        columns: [
          {
            name: 'api_key_id',
            align: 'left',
            label: 'API Key ID',
            field: 'api_key_id'
          },
          {
            name: 'name',
            align: 'left',
            label: 'Name',
            field: 'name'
          },
          {
            name: 'fiat_currency',
            align: 'left',
            label: 'Fiat Currency',
            field: 'fiat_currency'
          },
          {
            name: 'exchange_rate_provider',
            align: 'left',
            label: 'Exchange Rate Provider',
            field: 'exchange_rate_provider'
          },
          {
            name: 'fee',
            align: 'left',
            label: 'Fee (%)',
            field: 'fee'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      formDialog: {
        show: false,
        fiatCurrencies: _.keys(window.atmbitbit_vars.fiat_currencies),
        exchangeRateProviders: _.keys(
          window.atmbitbit_vars.exchange_rate_providers
        ),
        data: _.clone(defaultValues)
      }
    }
  },
  computed: {
    sortedAtmBitBits: function () {
      return this.atmbitbits.sort(function (a, b) {
        // Sort by API Key ID alphabetically.
        var apiKeyId_A = a.api_key_id.toLowerCase()
        var apiKeyId_B = b.api_key_id.toLowerCase()
        return apiKeyId_A < apiKeyId_B ? -1 : apiKeyId_A > apiKeyId_B ? 1 : 0
      })
    }
  },
  methods: {
    getAtmBitBits: function () {
      var self = this
      LNbits.api
        .request(
          'GET',
          '/atmbitbit/api/v1/atmbitbits?all_wallets=true',
          this.g.user.wallets[0].adminkey
        )
        .then(function (response) {
          self.atmbitbits = response.data.map(function (obj) {
            return mapAtmBitBit(obj)
          })
        })
        .catch(function (error) {
          clearInterval(self.checker)
          LNbits.utils.notifyApiError(error)
        })
    },
    closeFormDialog: function () {
      this.formDialog.data = _.clone(defaultValues)
    },
    exportConfigFile: function (atmbitbitId) {
      var atmbitbit = _.findWhere(this.atmbitbits, {id: atmbitbitId})
      var fieldToKey = {
        api_key_id: 'apiKey.id',
        api_key_secret: 'apiKey.key',
        api_key_encoding: 'apiKey.encoding',
        fiat_currency: 'fiatCurrency'
      }
      var lines = _.chain(atmbitbit)
        .map(function (value, field) {
          var key = fieldToKey[field] || null
          return key ? [key, value].join('=') : null
        })
        .compact()
        .value()
      lines.push('callbackUrl=' + window.atmbitbit_vars.callback_url)
      lines.push('shorten=true')
      var content = lines.join('\n')
      var status = Quasar.utils.exportFile(
        'atmbitbit.conf',
        content,
        'text/plain'
      )
      if (status !== true) {
        Quasar.plugins.Notify.create({
          message: 'Browser denied file download...',
          color: 'negative',
          icon: null
        })
      }
    },
    openUpdateDialog: function (atmbitbitId) {
      var atmbitbit = _.findWhere(this.atmbitbits, {id: atmbitbitId})
      this.formDialog.data = _.clone(atmbitbit._data)
      this.formDialog.show = true
    },
    sendFormData: function () {
      var wallet = _.findWhere(this.g.user.wallets, {
        id: this.formDialog.data.wallet
      })
      var data = _.omit(this.formDialog.data, 'wallet')
      if (data.id) {
        this.updateAtmBitBit(wallet, data)
      } else {
        this.createAtmBitBit(wallet, data)
      }
    },
    updateAtmBitBit: function (wallet, data) {
      var self = this
      LNbits.api
        .request(
          'PUT',
          '/atmbitbit/api/v1/atmbitbit/' + data.id,
          wallet.adminkey,
          _.pick(data, 'name', 'fiat_currency', 'exchange_rate_provider', 'fee')
        )
        .then(function (response) {
          self.atmbitbits = _.reject(self.atmbitbits, function (obj) {
            return obj.id === data.id
          })
          self.atmbitbits.push(mapAtmBitBit(response.data))
          self.formDialog.show = false
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    createAtmBitBit: function (wallet, data) {
      var self = this
      LNbits.api
        .request('POST', '/atmbitbit/api/v1/atmbitbit', wallet.adminkey, data)
        .then(function (response) {
          self.atmbitbits.push(mapAtmBitBit(response.data))
          self.formDialog.show = false
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    deleteAtmBitBit: function (atmbitbitId) {
      var self = this
      var atmbitbit = _.findWhere(this.atmbitbits, {id: atmbitbitId})
      LNbits.utils
        .confirmDialog(
          'Are you sure you want to delete "' + atmbitbit.name + '"?'
        )
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/atmbitbit/api/v1/atmbitbit/' + atmbitbitId,
              _.findWhere(self.g.user.wallets, {id: atmbitbit.wallet}).adminkey
            )
            .then(function (response) {
              self.atmbitbits = _.reject(self.atmbitbits, function (obj) {
                return obj.id === atmbitbitId
              })
            })
            .catch(function (error) {
              LNbits.utils.notifyApiError(error)
            })
        })
    }
  },
  created: function () {
    if (this.g.user.wallets.length) {
      var getAtmBitBits = this.getAtmBitBits
      getAtmBitBits()
      this.checker = setInterval(function () {
        getAtmBitBits()
      }, 20000)
    }
  }
})
